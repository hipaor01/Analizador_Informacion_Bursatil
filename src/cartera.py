import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import textwrap
import sys
import seaborn as sns
from seriePrecios import SeriePrecios
from data_utils import build_corr_matrix, get_simulacion_valores, save_csv, normalizar_texto

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
    ax.pie(tamanios, labels=etiquetas, explode=resalte, autopct="%1.1f%%", startangle=90, shadow=True)
    ax.set_title(titulo)
    #Queremos que se visualize un círculo perfecto
    ax.axis("equal")
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


class Cartera:
    #El parámetro archivosCSV va a contener una lista de ficheros CSV generados por extractor.py, y rutaCSV el directorio donde se encuentran todos ellos
    #Los atributos van a ser:
    #Activos: Lista de activos que componen la cartera
    #NumActivos: Número de activos
    #Pesos: Lista de pesos de cada uno de los activos en la cartera
    #ReturnsCartera: Serie con los retornos logarítmicos de todos los activos de la cartera para el período considerado
    #MatrizCorrelacion: Matriz de correlación de los activos de la cartera
    #NombreCartera: Nombre con el que queremos identificar a la cartera    
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

            #Debe haber tantos pesos como activos tenga la cartera
            if self.numActivos != len(pesos):
                print("Debe haber tantos pesos como activos tenga la cartera")
                return
            
            #Los pesos deben sumar 1
            pesosArray = np.array(pesos)
            if np.sum(pesosArray) != 1:
                print("Los pesos deben sumar 1")
                return
            self.pesos = pesosArray
            
            #Juntamos las series de retornos de cada uno de los activos en un único dataframe
            self.returnsCartera = pd.concat([pd.Series(self.activos[i].obtenerReturns()) for i in range(self.numActivos)], axis=1)
            #Calculamos la matriz de correlación de los retornos
            self.matrizCorrelacion = build_corr_matrix(self.returnsCartera)

            self.nombreCartera = nombreCartera
        except Exception as e:
            print("Alguno de los archivos pasados no es válido")

    #Devuelve el activo que se encuentre en la posición correspondiente en la cartera, debiendo estar entre 0 y numActivos - 1
    def obtenerActivo(self, posicion):
        if posicion < 0 or posicion >= self.numActivos:
            print("La posición debe estar entre 0 y " + str(self.numActivos - 1))
            return None
        
        return self.activos[posicion]

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--rutaCSV', type=str, required=True, help='Ruta de almacenamiento de los CSVs')
    parser.add_argument('--archivosSeries', nargs='+', type=str, required=True, help='CSVs conteniendo series de precios')
    parser.add_argument('--pesos', nargs='+', type=float, required=True, help='Pesos de cada serie de precios')
    parser.add_argument('--nombreCartera', type=str, required=True, help='Nombre que le queremos asignar a la cartera')
    parser.add_argument('--informe', type=str, required=True, help='Generar informe en formato markdown')
    args = parser.parse_args()

    cartera = Cartera(args.archivosSeries, args.rutaCSV, args.pesos, args.nombreCartera)
    
    #Las respuestas posibles al parámetro informe son si o no. Normalizamos el texto para permitir tildes y mayúsculas
    informeNormalizado = normalizar_texto(args.informe)
    if informeNormalizado != "si" and informeNormalizado != "no":
        print("La respuesta a si quiere generar un informe acerca de la cartera debe ser Sí o No")
        sys.exit(1)

    if informeNormalizado == "si":
        cartera.report()

    cartera.plots_report()
    
