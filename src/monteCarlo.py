import argparse
import sys
import json
from data_utils import exists_route, normalizar_texto, load_json
from cartera import Cartera

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--rutaCSV', type=str, required=True, help='Ruta de almacenamiento de los CSVs')
    parser.add_argument('--medias', nargs='+', type=float, required=False, help='Medias de cada una de las series que se quiere imponer')
    parser.add_argument('--desviacionesTipicas', nargs='+', type=float, required=False, help='Desviaciones típicas de cada una de las series que se quiere imponer')
    parser.add_argument('--numSimulaciones', type=int, required=True, help='Número de simulaciones que de desea realizar')
    parser.add_argument('--numDias', type=int, required=True, help='Número de días a lo largo de los cuales se va a realizar cada simulación')
    parser.add_argument('--valorInicial', type=float, required=True, help='Valor inicial del valor/cartera')
    parser.add_argument('--carteraCompleta', type=str, required=True, help='Indicar si se quiere simular la cartera en su conjunto o componente a componente')
    parser.add_argument('--nombreCartera', type=str, required=True, help='Nombre que le queremos asignar a la cartera')
    args = parser.parse_args()

    #Recuperamos una instancia de la clase Cartera creada anteriormente desde un json, usando el nombre de la cartera pasado por el usuario
    json_str = load_json(args.nombreCartera + ".json")
    if json_str == None:
        print("Ha habido un error al cargar la cartera solicitada")
        sys.exit(1)

    data = json.loads(json_str)
    cartera = Cartera.from_dict(data)
    numActivos = cartera.obtenerNumActivos()

    #Si el usuario no pasa medias como parámetro, lo que haremos será cojer las medias de los retornos de cada una de las series temporales, que son estimadores
    #insesgados de la media de la distribución que siguen
    medias = []
    if not args.medias:
        medias = [cartera.obtenerActivo(i).obtenerMedia() for i in range(numActivos)]
    else:
        medias = args.medias

    #Si el usuario no pasa desviaciones típicas como parámetro, lo que haremos será cojer las cuasidesviaciones típicas de los retornos de cada una de las series
    #temporales, que son estimadores insesgados de la desviación típica de la distribución que siguen
    desviacionesTipicas = []
    if not args.desviacionesTipicas:
        desviacionesTipicas = [cartera.obtenerActivo(i).obtenerCuasiDesviacionTipica() for i in range(numActivos)]
    else:
        desviacionesTipicas = args.desviacionesTipicas

    #La respuesta a si se quiere simular la cartera completa o no debe ser si o no. Normalizamos el texto para permitir tildes y mayúsculas
    carteraCompletaNormalizada = normalizar_texto(args.carteraCompleta)
    if carteraCompletaNormalizada != "si" and carteraCompletaNormalizada != "no":
        print("La respuesta a si se quiere simular la cartera completa o no debe ser Sí o No")
        sys.exit(1)
    
    carteraCompletadaBool = False
    if carteraCompletaNormalizada == "si":
        carteraCompletadaBool = True
    

    #Realizamos la simulación de acuerdo a lo indicado por el usuario
    cartera.simulacionMonteCarlo(medias, desviacionesTipicas, args.numSimulaciones, args.numDias, args.valorInicial, carteraCompletadaBool, args.rutaCSV)




