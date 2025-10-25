import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from data_utils import get_log_returns
from scipy.stats import skew,kurtosis
from datetime import datetime

class SeriePrecios:
    #El parámetro archivoCSV va a contener un fichero CSV generado por extractor.py
    #Los atributos van a ser:
    #NombreActivo: Nombre del activo cuya serie temporal estamos cargando
    #Dates: Lista de fechas de la serie temporal
    #Longitud: Número de entradas en la serie temporal
    #ClosePrices: Lista de precios de cierre de la serie temporal
    #HighPrices: Lista de precios máximos de la serie temporal
    #LowPrices: Lista precios mínimos de la serie temporal
    #OpenPrices: Lista precios de apertura de la serie temporal
    #Volume: Lista de volúmenes negociados de la serie temporal
    #LogReturns: Retornos logarítmicos de la serie temporal (los escojemos en lugar de los simples porque se distribuyen normalmente, lo que nos va a ser útil para
    #Media: Media de los retornos logarítmicos
    #DesviacionTipica: Desviación típica de los retornos logarítmicos
    #CuasiDesviacionTipica: Cuasidesviacíon típica de los retornos logarítmicos (nos va a servir para estimar la desviación típica de la distribución que siguen 
    #los retornos logarítmicos) 
    #Monte Carlo)
    #Asimetria: Simetría de los retornos logarítmicos respecto de su media
    #Curtosis: Nivel de aplanamiento de los retornos logarítmicos respecto a una distribución normal
    def __init__(self, archivoCSV):
        try:
            data = pd.read_csv(archivoCSV)
            #Recordemos que el formato de los CSV es api_activo_fechaInicio_fechaFin, y que lleva delante todo el nombre de la ruta
            self.nombreActivo = (archivoCSV.split('\\')[-1]).split('_')[1] 
            self.dates = data['Date'].to_numpy()
            self.longitud = self.dates.shape[0]
            self.closePrices = data['Close'].to_numpy()
            self.highPrices = data['High'].to_numpy()
            self.lowPrices = data['Low'].to_numpy()
            self.openPrices = data['Open'].to_numpy()
            self.volume = data['Volume'].to_numpy()
            self.logReturns = get_log_returns(self.closePrices)
            self.calcularMedia()
            self.calcularDesviacionTipica()
            self.calcularCuasiDesviacionTipica()
            self.calcularAsimetria()
            self.calcularCurtosis()
        except Exception as e:
            print("El archivo " + archivoCSV + " no es válido")

    #Obtención del nombre del activo
    def obtenerNombreActivo(self):
        return self.nombreActivo
    
    #Obtención de la primera fecha en la serie temporal, en formato Día/Mes/Año
    def obtenerPrimeraFecha(self):
        return datetime.strptime(self.dates[0], "%Y-%m-%d")
    
    #Obtención de la última fecha en la serie temporal, en formato Día/Mes/Año
    def obtenerUltimaFecha(self):
        return datetime.strptime(self.dates[-1], "%Y-%m-%d")

    #Obtención de los retornos logarítmicos
    def obtenerReturns(self):
        return self.logReturns

    #Cálculo de la media de los retornos logarítmicos
    def calcularMedia(self):
        self.media = np.mean(self.logReturns)

    #Obtención de la media de los retornos logarítmicos
    def obtenerMedia(self):
        return self.media
    
    #Cálculo de la desviación típica de los retornos logarítmicos
    def calcularDesviacionTipica(self):
        self.desviacionTipica = np.std(self.logReturns)

    #Obtención de la desviación típica de los retornos logarítmicos
    def obtenerDesviacionTipica(self):
        return self.desviacionTipica

    #Cálculo de la cuasidesviación tipica de los retornos logarítmicos
    def calcularCuasiDesviacionTipica(self):
        self.cuasiDesviacionTipica =  (self.longitud/(self.longitud - 1)) * self.desviacionTipica

    #Obtención de la cuasidesviación típica de los retornos logarítmicos
    def obtenerCuasiDesviacionTipica(self):
        return self.cuasiDesviacionTipica
    
    #Cálculo y obtención de las medias móviles simples de precios de cierre de n días
    def obtenerMediaMovilSimple(self, n):
        #n debe ser positivo y menor o igual que la longitud de la serie
        if n <= 0 or n > self.longitud:
            print("El número de días debe ser positivo y menor o igual que la longitud de la serie")
            return np.array([])

        mediaMovil = np.convolve(self.closePrices, np.ones(n)/n, mode='valid')
        return mediaMovil
    
    #Cálculo de la asimetría de los retornos logarítmicos
    def calcularAsimetria(self):
        self.asimetria = skew(self.logReturns)

    #Obtención de la asimetría de los retornos logarítmicos
    def obtenerAsimetria(self):
        return self.asimetria 
    
    #Cálculo de la curtosis de los retornos logarítmicos 
    def calcularCurtosis(self):
        self.curtosis = kurtosis(self.logReturns)

    #Obtención de la curtosis de los retornos logarítmicos
    def obtenerCurtosis(self):
        return self.curtosis

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--archivoSerie', type=str, required=True, help='CSV conteniendo serie de precios')
    args = parser.parse_args()

    serie = SeriePrecios(args.archivoSerie)
    
