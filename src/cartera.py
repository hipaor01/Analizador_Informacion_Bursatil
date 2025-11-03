import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import textwrap
import sys
import seaborn as sns
import json
import datetime
from seriePrecios import SeriePrecios
from data_utils import build_corr_matrix, get_simulacion_valores, save_csv, save_json, normalizar_texto
from dataclasses import dataclass, asdict
from typing import List

#Función para visualizar en un gráfico las simulaciones realizadas para un valor o cartera
def grafica_simulaciones(data, titulo):
    data.plot(figsize=(10,5))
    plt.title(titulo)
    #Imponemos que las etiquetas del eje de abscisas sean números enteros, ya que representan días
    plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    plt.xlabel("Días")
    plt.ylabel("Valores")
    plt.legend(title="Simulaciones")
    plt.grid(True)
    plt.show()

#Función para visualizar un diagrama de sectores, dadas una lista de etiquetas, sus correspondientes tamaños en el diagrama (sobre 100) y el título que deseemos ponerle
def grafica_sectores(etiquetas, tamanios, titulo):
    if len(etiquetas) != len(tamanios):
        print("Debe haber el mismo número de etiquetas que de tamaños")
        return False
    
    if np.sum(np.array(tamanios)) != 100:
        print("El total de los tamaños debe sumar 100")
        return False
    
    #Queremos que se ordenen por los tamaños, de mayor a menor
    ordenados = sorted(zip(etiquetas, tamanios), key=lambda x: x[1], reverse=True)
    etiquetas_ordenados, tamanios_ordenados = zip(*ordenados)

    #Indicamos que se resalte el sector más grande
    resalte = np.zeros(len(etiquetas)).tolist()
    resalte[0] = 0.05

    fig, ax = plt.subplots(figsize=(5,5))
    #Indicamos que se muestre el porcentaje de cada sector, que empiece en la parte superior y que tenga sombra
    ax.pie(tamanios_ordenados, labels=etiquetas_ordenados, explode=resalte, autopct="%1.1f%%", startangle=90, shadow=True)
    ax.set_title(titulo)
    #Queremos que se visualize un círculo perfecto
    ax.axis("equal")
    plt.show()

    return True

#Función para visualizar la media móvil de una cartera con una ventana de n días
def grafica_media_movil(n,cartera):
    activos = cartera.obtenerActivos()
    pesos = cartera.obtenerPesos()
    fechas = cartera.obtenerFechas()

    #Comprobamos que n es mayor que 0 y menor o igual que el número de fechas
    if n <= 0 or n > fechas.shape[0]:
        print("El tamaño de la ventana debe ser mayor que 0 y menor o igual que el número de entradas de la serie")
        return False

    #Como estamos usando media móvil simple y las series temporales de los activos están alineadas temporalmente, podemos calcular
    #la media móvil de la cartera como la suma ponderada de las medias móviles de sus activos.
    mediasMoviles = np.vstack([activo.obtenerMediaMovilSimple(n) for activo in activos])
    mediasMovilesPonderadas = np.sum(mediasMoviles*pesos[:,np.newaxis],axis=0)
    #Para ver la tendencia de la cartera, visualizamos la media móvil junto con los precios de cierre
    preciosCierre = np.vstack([activo.obtenerClosePrices() for activo in activos])
    preciosCierrePonderados = np.sum(preciosCierre*pesos[:,np.newaxis],axis=0)


    plt.figure(figsize=(10,6))
    plt.plot(fechas,preciosCierrePonderados, label="Valor cartera", color='steelblue')
    #Como es media móvil de n días, no tenemos entrada de fecha hasta el día n del período
    plt.plot(fechas[n-1:],mediasMovilesPonderadas, label="Media móvil " +  str(n) + " días", color='orange', linewidth=2)
    plt.xlabel("Fecha")
    plt.ylabel("Valor ponderado")
    plt.title("Evolución de " + cartera.obtenerNombreCartera() + " y su media móvil (" + str(n) + " días)")
    plt.legend()
    plt.show()

    return True

#Función para visualizar el RSI de las componentes de una cartera, con una ventana de 14 días
def grafica_RSI_activos(cartera):
        fechas = cartera.obtenerFechas()

        #Comprobamos que el número de fechas es mayor o igual que 15
        if fechas.shape[0] < 15:
            print("El número de entradas en las series temporales de los activos debe ser mayor o igual que 15")
            return False
    
        for activo in cartera.activos:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,7), sharex=True, gridspec_kw={'height_ratios':[3,1]})

            ax1.plot(fechas, activo.obtenerClosePrices(), label="Precio", color="steelblue")
            ax1.set_title("Precio y RSI (14 días) " + activo.obtenerNombreActivo())
            ax1.set_ylabel("Precio (USD)")
            ax1.legend(loc="upper left")

            #Como hemos calculado el RSI con ventana de 14 días, no tenemos entrada de fecha hasta el día 15 del período estudiado
            ax2.plot(fechas[14:],activo.obtenerRSI(), color='darkorange', label='RSI (14 días)')
            ax2.axhline(70, color='red', linestyle='--', linewidth=1)
            ax2.axhline(30, color='green', linestyle='--', linewidth=1)
            ax2.fill_between(fechas[14:], 70, 100, color='red', alpha=0.1)
            ax2.fill_between(fechas[14:], 0, 30, color='green', alpha=0.1)
            ax2.set_ylabel("RSI")
            ax2.set_xlabel("Fecha")
            ax2.set_ylim(0, 100)
            ax2.legend(loc="upper left")

            plt.tight_layout()
            plt.show()

            return True


#Función para visualizar una matriz de correlación mediante un mapa de calor, dadas también las etiquetas cuya correlación está representada por la matriz
def mapa_calor(matriz_corr, etiquetas, titulo):
    if not np.array_equal(matriz_corr.T, matriz_corr):
        print("La matriz de correlación debe ser simétrica")
        return False
    
    #Como es simétrica, es igual comparar por su número de filas que por su número de columnas
    if len(etiquetas) != matriz_corr.shape[0]:
        print("Debe haber tantas etiquetas como filas/columnas tiene la matriz de correlación")
        return False
    
    sns.heatmap(matriz_corr, annot=True, xticklabels=etiquetas, yticklabels=etiquetas, cmap="coolwarm", center=0)
    plt.title(titulo)
    plt.show()

    return True

@dataclass
class Cartera:
    #El parámetro archivosCSV va a contener una lista de ficheros CSV generados por extractor.py, y rutaCSV el directorio donde se encuentran todos ellos
    #Los atributos van a ser:
    #Activos: Lista de activos que componen la cartera
    #NumActivos: Número de activos
    #Pesos: Lista de pesos de cada uno de los activos en la cartera
    #ReturnsCartera: Serie con los retornos logarítmicos de todos los activos de la cartera para el período considerado
    #MatrizCorrelacion: Matriz de correlación de los activos de la cartera
    #ClosePonderado: Lista de precios ponderados de cierre para la cartera
    #Dates: Lista de fechas de las series de precios que componen la cartera
    #NombreCartera: Nombre con el que queremos identificar a la cartera

    activos: List[SeriePrecios]
    numActivos: int
    pesos: np.array
    returnsCartera: pd.DataFrame
    matrizCorrelacion: np.array
    closePonderado: np.array
    dates: np.array
    nombreCartera: str

    def __init__(self, archivosCSV, rutaCSV, pesos, nombreCartera):
        try:
            #Debemos comprobar en primer lugar que los archivos CSV compartidos son de activos distintos
            #Recordemos que el formato de los CSV es api_activo_fechaInicio_fechaFin
            activos = [archivo.split('_')[1] for archivo in archivosCSV]
            if len(set(activos)) != len(activos):
                print("No puede haber activos repetidos")
                return
            
            self.numActivos = len(activos)
            
            #Debemos comprobar que todas las fechas de inicio son iguales, y lo mismo con las de fin
            fechasInicio = [archivo.split('_')[2] for archivo in archivosCSV]
            if len(set(fechasInicio)) != 1:
                print("La fecha de inicio del período en todos los archivos debe ser la misma")
                return

            
            fechasFin = [archivo.split('_')[3] for archivo in archivosCSV]
            if len(set(fechasFin)) != 1:
                print("La fecha de fin del período en todos los archivos debe ser la misma")
                return
            
            #Vamos introduciendo en la lista todas las instancias de SeriePrecios creadas
            self.activos = [SeriePrecios(rutaCSV + "\\" + archivo) for archivo in archivosCSV]

            #Como las fechas son las mismas para todos los activos, cojemos el primero por ejemplo, y los pasamos a formato datetime
            self.dates = np.array(self.activos[0].obtenerFechas(), dtype='datetime64[D]')

            #Debe haber tantos pesos como activos tenga la cartera
            if self.numActivos != len(pesos):
                print("Debe haber tantos pesos como activos tenga la cartera")
                return
            
            #Los pesos deben sumar 1
            self.pesos = np.array(pesos)
            if np.sum(self.pesos) != 1:
                print("Los pesos deben sumar 1")
                return
            
            #Juntamos las series de retornos de cada uno de los activos en un único dataframe
            self.returnsCartera = pd.concat([pd.Series(self.activos[i].obtenerReturns()) for i in range(self.numActivos)], axis=1)
            #Calculamos la matriz de correlación de los retornos
            self.matrizCorrelacion = build_corr_matrix(self.returnsCartera)

            preciosCierre = np.vstack([activo.obtenerClosePrices() for activo in self.activos])
            self.closePonderado = np.sum(preciosCierre*self.pesos[:,np.newaxis],axis=0)

            self.nombreCartera = nombreCartera
        except Exception as e:
            print("Alguno de los archivos pasados no es válido")

    #Devuelve el activo que se encuentre en la posición correspondiente en la cartera, debiendo estar entre 0 y numActivos - 1
    def obtenerActivo(self, posicion):
        if posicion < 0 or posicion >= self.numActivos:
            print("La posición debe estar entre 0 y " + str(self.numActivos - 1))
            return None
        
        return self.activos[posicion]
    
    #Devuelve todos los activos de la cartera
    def obtenerActivos(self):
        return self.activos
    
    #Devuelve todas las fechas de las series de precios que componen la cartera
    def obtenerFechas(self):
        return self.dates
    
    #Devuelve todos los pesos de la cartera
    def obtenerPesos(self):
        return self.pesos
    
    #Devuelve el nombre de la cartera
    def obtenerNombreCartera(self):
        return self.nombreCartera
    
    #Devuelve el número de activos que componen la cartera
    def obtenerNumActivos(self):
        return self.numActivos
    

    #Simulación de un proceso de Monte Carlo para los valores de una cartera
    #Medias: Lista de medias de retornos logarítmicos para cada uno de los activos que componen la cartera
    #Desviaciones_Tipicas: Lista de desviaciones típicas de retornos
    #ValorInicial: Valor inicial de la cartera
    #CarteraCompleta: Si está a True querrá decir que queremos que se simule la cartera en su conjunto, mientras que si está a False indicará que queremos
    #que se haga por cada activo por separado
    #DirectorioCSV: Carpeta donde se desea guardar todos los CSV generados por esta función
    def simulacionMonteCarlo(self, medias, desviaciones_tipicas, numSimulaciones, numDias, valorInicial, carteraCompleta, directorioCSV):
        #Inicializamos el nombre de las columnas de los dataframes que vamos a generar
        nombreColumnas = ['Simulación ' + str(i+1) for i in range(numSimulaciones)]

        #La longitud de la lista de medias debe ser igual al número de activos de la cartera
        if len(medias) != self.numActivos:
            print("Deben pasarse tantas medias como activos tiene la cartera")
            return
        
        #Lo mismo con la lista de desviaciones típicas
        if len(desviaciones_tipicas) != self.numActivos:
            print("Deben pasarse tantas desviaciones típicas como activos tiene la cartera")
            return
        
        #El número de simulaciones debe ser positivo
        if numSimulaciones <= 0:
            print("El número de simulaciones debe ser positivo")
            return
        
        #Lo mismo para el número de días
        if numDias <= 0:
            print("El número de días debe ser positivo")
            return
        
        #Lo mismo para el valor inicial
        if valorInicial <= 0:
            print("El valor inicial de la cartera debe ser positivo")
            return

        if carteraCompleta:
            #Usamos las propiedades de la combinación lineal de distribuciones normales
            mediaCartera = self.pesos @ medias
            #Calculamos la matriz de covarianzas para las desviaciones típicas dadas
            matrizCovarianzas = self.matrizCorrelacion * np.outer(desviaciones_tipicas,desviaciones_tipicas)
            #Usamos de nuevo las propiedades de la distribución normal
            desviacionTipicaCartera = np.sqrt(self.pesos @ matrizCovarianzas @ self.pesos.T)
            simulacion = get_simulacion_valores(mediaCartera, desviacionTipicaCartera, numSimulaciones, numDias, valorInicial)
            #Juntamos en un único dataframe todas las simulaciones, siendo cada una de las columnas una simulación
            dataframeSimulacion = pd.concat([pd.Series(simulacion[i]) for i in range(simulacion.shape[0])], axis=1)
            dataframeSimulacion.columns = nombreColumnas
            #Guardamos el dataframe en un .csv
            save_csv(dataframeSimulacion, directorioCSV + "\\" + self.nombreCartera + ".csv", False)
            grafica_simulaciones(dataframeSimulacion, self.nombreCartera)
        else:
            for i in range(self.numActivos):
                #Como valor inicial le pasamos la parte proporcional al peso que tenga el activo en la cartera
                simulacion = get_simulacion_valores(medias[i], desviaciones_tipicas[i], numSimulaciones, numDias, self.pesos[i]*valorInicial)
                dataframeSimulacion = pd.concat([pd.Series(simulacion[i]) for i in range(simulacion.shape[0])], axis=1)
                dataframeSimulacion.columns = nombreColumnas
                #Al nombre escogido para la cartera le añadimos el del activo que estamos 
                nombreArchivo = self.nombreCartera + "_" + self.activos[i].obtenerNombreActivo()
                save_csv(dataframeSimulacion, directorioCSV + "\\" + nombreArchivo + ".csv", False)
                grafica_simulaciones(dataframeSimulacion, nombreArchivo)

    #Método para generar un informe de la información más relevante de la cartera
    def report(self):
        #Con textwrap hacemos que se ignoren los espacios previos al comienzo del texto
        texto = textwrap.dedent(f"""
                # Informe de la cartera **{self.nombreCartera}** 
                ## Número de activos: **{self.numActivos}**
        """)

        for i in range(self.numActivos):
            texto += f"### Activo {i+1}\n\n"
            texto += f"Nombre: **{self.activos[i].obtenerNombreActivo()}**  \n"
            texto += f"Peso en la cartera: **{self.pesos[i]}**  \n"
            texto += f"Período considerado: **{self.activos[i].obtenerPrimeraFecha().strftime('%d/%m/%Y')} - {self.activos[i].obtenerUltimaFecha().strftime('%d/%m/%Y')}**  \n"
            #Incluimos también texto en LaTeX
            texto += f"Retornos: **$\\mu = {self.activos[i].obtenerMedia(): .6f}$**, "
            texto += f"**$\\sigma = {self.activos[i].obtenerDesviacionTipica(): .6f}$**, "
            texto += f"**$g_1 = {self.activos[i].obtenerAsimetria(): .6f}$**, "
            texto += f"**$g_2 = {self.activos[i].obtenerCurtosis(): .6f}$**\n\n"

        texto +=f"### Correlaciones entre activos\n\n"
        for i in range(self.matrizCorrelacion.shape[0]):
            for j in range(self.matrizCorrelacion.shape[1]):
                #Ignoramos los elementos de la diagonal principal y los que se encuentren por debajo de ella (evitando valores repetidos)
                if i != j and i < j:
                    #Si estamos en una posición distinta a la primera, añadimos una coma y espacio al principio
                    if i != 0 or j != 1:
                        texto += ", "
                    texto += f"**$\\rho_{{{i+1}{j+1}}} = {self.matrizCorrelacion[i][j]: .6f}$**"
                else:
                    continue

        try:
            nombreMd = "informe" + self.nombreCartera + ".md" 
            with open(nombreMd, "w", encoding="utf-8") as f:
                f.write(texto)
            print("Archivo " + nombreMd + " generado correctamente")
        except Exception as e:
            print("Hubo un error al intentar generar " + nombreMd)

    def plots_report(self):
        nombresActivos = [self.activos[i].obtenerNombreActivo() for i in range(self.numActivos)]

        if not grafica_sectores(nombresActivos, self.pesos*100, "Pesos " + self.nombreCartera):
            print("Error al visualizar distribución de pesos entre los activos de la cartera")
            return
        
        if not mapa_calor(self.matrizCorrelacion, nombresActivos, "Correlaciones " + self.nombreCartera):
            print("Error al visualizar mapa de calor de las correlaciones entre los activos de la cartera")
            return
        
        #En este caso hemos elegido una ventana de 20 días
        if not grafica_media_movil(20, self):
            print("Error al visualizar media móvil de 20 días para la cartera")
            return
        
        if not grafica_RSI_activos(self):
            print("Error al visualzizar RSI de las componentes de la cartera")
            return

        
    #Este método nos va a ayudar a poder serializar en un json campos de tipo dataframe
    def to_dict(self):
        return {
            "activos": [activo.to_dict() for activo in self.activos],
            "numActivos": self.numActivos,
            "pesos": self.pesos.tolist(),
            "returnsCartera": self.returnsCartera.to_dict(orient="records"),
            "matrizCorrelacion": self.matrizCorrelacion.tolist(),
            "closePonderado": self.closePonderado.tolist(),
            "dates": [str(fecha) for fecha in self.dates],
            "nombreCartera": self.nombreCartera
        }
    
    @classmethod
    #Este método de clase nos va a ayudar a desearilizar el json generado por la función anterior. Se declara de clase porque cuando lo llamamos aun no 
    #hay ninguna instancia de la clase creada
    def from_dict(cartera, datos):
        #No podemos llamar al constructor por defecto que crea dataclass porque ya lo hemos sobreescrito
        obj = cartera.__new__(cartera)

        obj.activos = [SeriePrecios.from_dict(activo) for activo in datos["activos"]]
        obj.numActivos = datos["numActivos"]
        obj.pesos = np.array(datos["pesos"])
        obj.returnsCartera = pd.DataFrame(datos["returnsCartera"])
        obj.matrizCorrelacion = np.array(datos["matrizCorrelacion"])
        obj.closePonderado = np.array(datos["closePonderado"])
        obj.dates = [np.datetime64(fecha) for fecha in datos["dates"]]
        obj.dates = np.array(datos["dates"])
        obj.nombreCartera = datos["nombreCartera"]

        return obj
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--rutaCSV', type=str, required=True, help='Ruta de almacenamiento de los CSVs')
    parser.add_argument('--archivosSeries', nargs='+', type=str, required=True, help='CSVs conteniendo series de precios')
    parser.add_argument('--pesos', nargs='+', type=float, required=True, help='Pesos de cada serie de precios')
    parser.add_argument('--nombreCartera', type=str, required=True, help='Nombre que le queremos asignar a la cartera')
    parser.add_argument('--informe', type=str, required=True, help='Generar informe en formato markdown')
    args = parser.parse_args()

    cartera = Cartera(args.archivosSeries, args.rutaCSV, args.pesos, args.nombreCartera)
    #Guardamos en json los datos sobre esta instancia de la clase Cartera, para luego recuperarla en el programa de simulaciones de Monte Carlo
    json_str = json.dumps(cartera.to_dict())
    save_json(args.nombreCartera + ".json", json_str)

    
    #Las respuestas posibles al parámetro informe son si o no. Normalizamos el texto para permitir tildes y mayúsculas
    informeNormalizado = normalizar_texto(args.informe)
    if informeNormalizado != "si" and informeNormalizado != "no":
        print("La respuesta a si quiere generar un informe acerca de la cartera debe ser Sí o No")
        sys.exit(1)

    if informeNormalizado == "si":
        cartera.report()

    cartera.plots_report()
    
