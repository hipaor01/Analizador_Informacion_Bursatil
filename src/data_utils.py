import numpy as np
import unicodedata
from pathlib import Path

#Función para obtener rendimientos logarítmicos dada una serie de precios
def get_log_returns(prices):
    returns = np.diff(np.log(prices))
    #Eliminamos posibles valores NaN
    returns = returns[~np.isnan(returns)]
    return returns

#Función para construir matriz de correlación a partir 
def build_corr_matrix(data):
    correlationMatrix = data.corr()
    correlationMatrixArray = correlationMatrix.to_numpy()
    return correlationMatrixArray

#Función para almacenar csvs a partir de un dataframe. El parámetro indeceColumna sirve para indicar si queremos que el índice se visualize como una columna más en el CSV o no
def save_csv(data, nombre, indiceColumna):
    try:
        #Codificación latin-1 para soportar las tildes
        data.to_csv(nombre, index=indiceColumna, encoding="latin-1")
        print("El archivo " + nombre + " fue creado con éxito")
    except Exception as e:
        print("Error al crear el archivo " + nombre)

#Función para comprobar si una ruta existe en nuestro equipo
def exists_route(ruta):
    if not Path(ruta).exists():
        return False
    else:
        return True
    
#Función para normalizar cadenas de caracteres, es decir, devolverlas en minúscula y sin tildes
def normalizar_texto(cadena):
    if not isinstance(cadena, str):
        return cadena
    cadena = cadena.strip().lower()
    cadena = ''.join(c for c in unicodedata.normalize('NFD', cadena) if unicodedata.category(c) != 'Mn')
    return cadena



#Función que realiza una simulación de Monte Carlo de los valores de un activo
#Media: Es la media de la distribución normal sobre la que se van a generar los retornos logarítmicos
#Desviacion_Tipica: Es la desviación típica de dicha distribución
#NumSimulaciones: Número de simulaciones de Monte Carlo a realizar
#NumDias: Número de días para los que se va a realizar cada simulación
#ValorInicial: Valor de partida para todas las simulaciones
def get_simulacion_valores(media, desviacion_tipica, numSimulaciones, numDias, valorInicial):
    try:
        #Son los retornos logarítmicos, no los simples, ya que son los que se distribuyen normalmente
        returns = np.random.normal(media, desviacion_tipica, (numSimulaciones,numDias))

        #Simulamos precios, teniendo en cuenta que los retornos logarítmicos son aditivos
        precios_simulados = valorInicial * np.exp(np.cumsum(returns, axis=1))

        return precios_simulados
    except Exception as e:
        print("Error al realizar simulación de precios")
        return np.array([])