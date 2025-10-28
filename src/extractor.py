import argparse
import sys
import yfinance as yf
import pandas as pd
import os
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from datetime import datetime, timedelta
from data_utils import save_csv, save_json, exists_route, normalizar_texto
from dotenv import load_dotenv

#Cargamos las variables de entorno guardadas en el .env
load_dotenv()
#En este caso solo tenemos la clave del API de alpha_vantage
claveAPI = os.getenv("API_KEY")


#Diccionario con acciones disponibles y sus abreviaturas para cada API
acciones = {"Apple" : "AAPL",
            "Microsoft": "MSFT",
            "Alphabet": "GOOGL",
            "Amazon": "AMZN",
            "Nvidia": "NVDA", 
            "JPMorgan": "JPM",
            "Golman Sachs": "GS",
            "Coca-Cola": "KO",
            "McDonald's": "MCD", 
            "Tesla": "TSLA", 
            "ExxonMobil": "XOM", 
            "Johnson & Johnson": "JNJ",
            "Pfizer": "PFE"}
#Diccionario con índices disponibles y sus abreviaturas para cada API, siendo la prmera la de yfinance y la segunda la de alpha_vantage (en este caso es la abreviatura
#de un ETF que replica al índice, no del índice en si mismo)
indices = {"S&P 500": ["^GSPC","SPY"], 
           "Nasdaq": ["^IXIC","QQQ"], 
           "Dow Jones": ["^DJI", "DIA"], 
           "Euro Stoxx": ["^STOXX50E", "FEZ"],
           "Nikkei": ["^N225", "EWJ"], 
           "IBEX 35": ["^IBEX", "EWP"]}
#Lista de apis disponibles
apis = ["yfinance", "alpha_vantage"]

#Función para validar que, dada una cadena de caracteres, se trata de una fecha válida
def validarFecha(fecha):
    try:
        fechaConvertida = datetime.strptime(fecha, "%d-%m-%Y")
        return fechaConvertida,True
    except ValueError:
        return None,False
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--accion', type=str, required=False, help='Acción individual de empresa')
    parser.add_argument('--indice', type=str, required=False, help='Índice de referencia')
    parser.add_argument('--api', type=str, required=True, help='API financiera a consultar')
    parser.add_argument('--fechasInicio', nargs='+', type=str, required=True, help='Fechas de inicio de los períodos a consultar')
    parser.add_argument('--fechasFinal', nargs='+', type=str, required=True, help='Fechas de finalización de los períodos a consultar')
    parser.add_argument('--rutaCSV', type=str, required=True, help='Ruta de almacenamiento de los CSVs generados')
    parser.add_argument('--infoExtra', type=str, required=True, help='Información general acerca de una empresa')
    parser.add_argument('--rutaJSON', type=str, required=False, help='Ruta de almacenamiento de los JSONs generados')
    args = parser.parse_args()

    #Hay que pasar o bien el nombre de una acción individual de empresa o bien el nombre de un índice de referencia
    if (not args.accion and not args.indice) or  (args.accion and args.indice):
        print("Debe introducir, o bien el nombre de una empresa, o bien el de un índice por favor")
        sys.exit(1)

    #En el caso de querer trabajar con acciones, debe ser una de las disponibles
    if args.accion:
        if not (args.accion in acciones.keys()):
            print("Debe elegir una empresa válida por favor")
            sys.exit(1)

    #En el caso de querer trabajar con índices, debe ser uno de los disponibles
    if args.indice:
        if not (args.indice in indices):
            print("Debe elegir un índice válido por favor")
            sys.exit(1)

    #La API elegida debe ser una de las disponibles
    if not (args.api in apis):
        print("Debe elegir un API válida por favor")
        sys.exit(1)

    #Fechas de inicio y de finalización en posiciones similares en sus respectivas listas formarán una pareja, que dará lugar a un período
    #Comprobamos que las dos listas de fechas tienen longitud similar
    if len(args.fechasInicio) != len(args.fechasFinal):
        print("Debe haber el mismo número de fechas de inicio que de fin")
        sys.exit(1)
    fInicioConvertidas = []
    fFinalConvertidas = []

    for i in range(len(args.fechasInicio)):
        #La fecha de inicio debe ser una fecha válida
        fInicioConvertida,Aceptada = validarFecha(args.fechasInicio[i])
        if not Aceptada:
            print("Debe elegir una fecha de inicio válida en la posición " + str(i+1))
            sys.exit(1)

        #La fecha de finalización debe ser una fecha válida
        fFinalConvertida,Aceptada = validarFecha(args.fechasFinal[i])
        if not Aceptada:
            print("Debe elegir una fecha de finalización válida en la posición " + str(i+1))
            sys.exit(1)

        #La fecha de inicio debe ser anterior a la de finalización
        if fFinalConvertida <= fInicioConvertida:
            print("La fecha de inicio debe ser anterior a la de finalización")
            sys.exit(1)

        fInicioConvertidas.append(fInicioConvertida)
        fFinalConvertidas.append(fFinalConvertida)

    #La carpeta donde se quieran almacenar los CSVs generados debe existir
    if not exists_route(args.rutaCSV):
        print("La ruta de los CSV introducida no existe")
        sys.exit(1)

    #Las respuestas posibles al parámetro infoExtra son si o no. Normalizamos el texto para permitir tildes y mayúsculas
    infoExtraNormalizada = normalizar_texto(args.infoExtra)
    if infoExtraNormalizada != "si" and infoExtraNormalizada != "no":
        print("La respuesta a si quiere información extra acerca de la empresa debe ser Sí o No")
        sys.exit(1)
    else:
        #Si lo seleccionado es un índice, no vamos a mostrar esta información extra
        if args.indice and infoExtraNormalizada == "si":
            print("No está disponible la información extra para un índice")
            sys.exit(1)

    #Si se ha pedido que se muestre información extra, debe pasarse también la ruta donde almacenar los JSONs generados
    if infoExtraNormalizada == "si" and not args.rutaJSON:
        print("Debe introducir una ruta para exportar los JSONs")
        sys.exit(1)


    #La carpeta donde se quieran almacenar los JSONs generados debe existir
    if infoExtraNormalizada == "si" and not exists_route(args.rutaJSON):
        print("La ruta de los JSON introducida no existe")
        sys.exit(1)
    

    #Convertirmos las fechas de inicio y de fin del formato dd-mm-yyyy a yyyy-mm-dd
    formatoFechas = "%Y-%m-%d"
    fIniciosFormato = [fecha.strftime(formatoFechas) for fecha in fInicioConvertidas]
    fFinalesFormato = [fecha.strftime(formatoFechas) for fecha in fFinalConvertidas]

    #Trabajamos con el diccionario de acciones o el de índices en función de lo demandado por el usuario
    ticker = args.accion if args.accion else args.indice
    diccionario = acciones if args.accion else indices
    nombresCSV = []
    dataList = []
    nombreAPI = ""

    #Nombre de las columnas de precios
    columnasPrecios = ['Close', 'High', 'Low', 'Open', 'Volume']

    #Creamos un diccionario común entre APIs para almacenar la información extra de una empresa, si es así requerido
    #por el usuario
    infoExtra = {"Name" : "",
                "Sector": "",
                "Industry": "",
                "Country": "",
                "Market Capitalization": "",
                "Dividend Yield": ""
                }
    nombreJSON = ""

    if args.api == "yfinance":
        #En el caso de que se haya escogido un índice, habrá que quedarse con el primer elemento de la lista asociada a la clave en cuestión
        activo = diccionario[ticker] if args.accion else diccionario[ticker][0]
        nombreAPI = "yfinance_" + ticker
        for i in range(len(fIniciosFormato)):
            #Si el usuario ha pedido trabajar con yfinance, añadimos 1 día a la fecha porque en la llamada al api se excluye la fecha final pasada
            fFinalesFormato[i] = (datetime.strptime(fFinalesFormato[i], formatoFechas) + timedelta(days=1)).strftime(formatoFechas)
            data = yf.download(activo, start=fIniciosFormato[i], end=fFinalesFormato[i])
            data = data[columnasPrecios]
            #Como solo consultamos una empresa/índice, nos quedamos solamente con el nombre del tipo de precio en cada columna
            data.columns = data.columns.get_level_values(0)
            #Cambiamos la precisión a 2 decimales como en el caso de alpha_vantage
            data = data.round({'Close': 2, 'High': 2, 'Low': 2, 'Open': 2})
            dataList.append(data)
            nombresCSV.append(nombreAPI + "_" + args.fechasInicio[i] + "_" + args.fechasFinal[i] + ".csv")

        if infoExtraNormalizada == "si":
            info = yf.Ticker(activo).info
            infoExtra["Name"] = info['longName']
            infoExtra["Sector"] = info['sector']
            infoExtra["Industry"] = info['industry']
            infoExtra["Country"] = info['country']
            infoExtra["Market Capitalization"] = info['marketCap']
            infoExtra["Dividend Yield"] = info['dividendYield']
            nombreJSON = nombreAPI + ".json"
    elif args.api == "alpha_vantage":
        ts = TimeSeries(key=claveAPI, output_format='pandas')
        #En el caso de que se haya escogido un índice, habrá que quedarse con el segundo elemento de la lista asociada a la clave en cuestión
        activo = diccionario[ticker] if args.accion else diccionario[ticker][1]
        ordenColumnas = ['4. close', '2. high', '3. low', '1. open', '5. volume']
        data, _ = ts.get_daily(symbol=activo, outputsize = 'full')
        #Imponemos el mismo orden que hay en lo devuelto por yfinance
        data = data[ordenColumnas]
        #Imponemos los mismos nombres de columnas que los devueltos en yfinance
        data.columns = columnasPrecios
        #Imponemos el mismo nombre de índice que en yfinance
        data = data.rename_axis('Date')
        #La columna Volume la ponemos como entero, para que no se muestre con el punto decimal
        data['Volume'] = data['Volume'].astype(int)
        nombreAPI = "alphaVantage_" + ticker
        for i in range(len(fIniciosFormato)):
            #Alpha Vantage, a diferencia de yfinance, no tiene parámetros para especificar un rango de fechas, por lo que debemos ordenar la serie temporal
            #que nos devuelve y luego quedarnos con el rango especificado por el usuario
            dataList.append(data.sort_index().loc[fIniciosFormato[i]:fFinalesFormato[i]])
            nombresCSV.append(nombreAPI + "_" + args.fechasInicio[i] + "_" + args.fechasFinal[i] + ".csv")

        if infoExtraNormalizada == "si":
            fd = FundamentalData(key=claveAPI, output_format='pandas')
            overview, meta = fd.get_company_overview(activo)
            #Como lo que nos devuelve overview para cada campo es un dataframe de una sola columna, nos quedamos con su contenido en la primera fila
            infoExtra["Name"] = overview['Name'].iloc[0]
            infoExtra["Sector"] = overview['Sector'].iloc[0]
            infoExtra["Industry"] = overview['Industry'].iloc[0]
            infoExtra["Country"] = overview['Country'].iloc[0]
            #Convertimos a entero al igual que es devuelto por yfinance
            infoExtra["Market Capitalization"] = int(overview['MarketCapitalization'].iloc[0])
            #Convertimos a float al igual que es devuelto por yfinance
            infoExtra["Dividend Yield"] = float(overview['DividendYield'].iloc[0])
            nombreJSON = nombreAPI + ".json"

    #Exportamos a csv las series temporales obtenidas. El parámetro indiceColumna está a True para que se incluya a la fecha como a una columna más
    for i in range(len(nombresCSV)):
        data = dataList[i]
        csv = nombresCSV[i]
        save_csv(data, args.rutaCSV +  "\\" + csv, True)

    if infoExtraNormalizada == "si":
        #Guardamos en un .json el contenido de infoExtra
        save_json(args.rutaJSON + "\\" + nombreJSON, infoExtra)
        


    

    
        


        

    


    


    
    

    