# Tarea_Bloque1_MIAX
Resolución de la tarea del bloque 1 del máster MIAX. Su contenido es el siguiente:

# .env.example
Ejemplo de fichero de variables de entorno .env, donde para el correcto funcionamiento del proyecto sería solamente necesario asignar valor a la variable API_KEY, que es la clave para conectarse al API de Alpha Vantage. Se puede obtener una de forma gratuita en https://www.alphavantage.co/support/#api-key.

# src 
Contiene todos los archivos .py:
- cartera.py: Este archivo contiene la definición de la clase Cartera, que representa una cartera compuesta por acciones de empresas e/o índices. Contiene métodos para realización de simulaciones de Monte Carlo, generación de informes y de gráficas.
- data_utils.py: Este archivo contiene la definición de varios métodos auxiliares que llevan a cabo tareas recurrentes.
- extractor.py: Programa encargado de la extracción de datos desde el API demandada por el usario, de su transformación y de su presentación final en formato csv y json.
- monteCarlo.py: Programa que permite realizar un número, especificado por el usuario, de simulaciones de Monte Carlo de una cartera en su conjunto o de cada una de sus componentes. Las simulaciones pueden ser moldeadas por el usuario, mediante parámetros como el valor de la cartera, las medias y desviaciones típicas de las componentes o el número de días de cada simulación.
- seriePrecios.py: Este archivo contiene la definición de la clase SeriePrecios, que representa una serie temporal de precios OHLC de acciones de una empresa o de un índice. También calcula varios estadísticos derivados de dichos precios.

La siguiente imagen representa el flujo de trabajo del proyecto, y como los programas y clases interaccionan entre sí:

![](Diagrama.png)

# Utilización
Las acciones disponibles para consultar van a ser las de las empresas: Apple, Microsoft, Alphabet, Amazon, Nvidia, JPMorgan, Goldman Sachs, Coca-Cola, McDonald's, Tesla, ExxonMobil, Johnson & Johnson, Pfizer. Por otro lado, los índices serán: S&P 500, Nasdaq, Dow Jones, Euro Stoxx, Nikkei, IBEX 35. Las APIs disponible son: yfinance y alpha_vantage. Comencemos por el extractor. Su modo de uso es el siguiente:

<pre lang="markdown"> python extractor.py --accion [Accion] --indice [Indice] --api [API] --fechasInicio [fechaInicio1] ... [fechaInicioN] --fechasFinal [fechaFinal1] ... [fechaFinalN] --rutaCSV [ruta] --infoExtra [Respuesta] --rutaJSON [ruta2] </pre>

Si queremos consultar las series de precios de Apple, en yfinance, para los períodos 23/12/2015-23/12/2016, 23/12/2017-23/12/2018 y que se exporten dichas series en csv al directorio C:\MiDirectorio:

<pre lang="markdown">python extractor.py --accion Apple --api yfinance --fechasInicio 23-12-2015 23-12-2017 --fechasFinal 23-12-2016 23-12-2018 --rutaCSV C:\MiDirectorio --infoExtra No</pre>

Si además queremos que se genere en un json información adicional de Apple, guardándose también en C:\MiDirectorio:

<pre lang="markdown">python extractor.py --accion Apple --api yfinance --fechasInicio 23-12-2015 23-12-2017 --fechasFinal 23-12-2016 23-12-2018 --rutaCSV C:\MiDirectorio --infoExtra Sí --rutaJSON C:\MiDirectorio</pre>

Si ahora en vez de una empresa lo que queremos es consultar la serie de precios de un índice, por ejemplo S&P 500 (importante, en el caso de nombres con el carácter & o con espacios, pasarlos entrecomillados), para las mismas fechas, api y rutas:

<pre lang="markdown">python extractor.py --indice "S&P 500" --api yfinance --fechasInicio 23-12-2015 23-12-2017 --fechasFinal 23-12-2016 23-12-2018 --rutaCSV C:\MiDirectorio --infoExtra No</pre>

Sigamos con la creación de una cartera. Su modo de uso es el siguiente:

<pre lang="markdown"> python cartera.py --rutaCSV [ruta] --archivosSeries [archivoSerie1] ... [archivoSerieN] --pesos [peso1] ... [pesoN] --nombreCartera [nombre] --informe [Respuesta] </pre>

Si queremos construir una cartera y visualizar algunas gráficas asociadas, a partir de las series temporales de Apple y S&P 500 obtenidas para el período 23/12/2015-23/12/2016, con pesos 0.6 y 0.4 respectivamente, llamando a la cartera Cartera1, y generando un informe de la cartera en un .md (dicho informe se genera en el mismo directorio de cartera.py, no en el de la ruta de los CSV):

<pre lang="markdown"> python cartera.py --rutaCSV C:\MiDirectorio --archivosSeries yfinance_Apple_23-12-2015_23-12-2016.csv "yfinance_S&P 500_23-12-2015_23-12-2016.csv" --pesos 0.6 0.4 --nombreCartera Cartera1 --informe Sí</pre>

Finalmente, veamos la simulación de Monte Carlo. Su modo de uso el siguiente:

<pre lang="markdown"> python monteCarlo.py --rutaCSV [ruta] --medias [media1] ... [mediaN] --desviacionesTipicas [desviacionTipica1] ... [desviacionTipicaN] --numSimulaciones [numSimulaciones] --numDias [numDias] --valorInicial [valorInicial] --carteraCompleta [carteraCompleta] --nombreCartera [nombreCartera] </pre>

Si queremos realizar 2 simulaciones de Cartera1 completa, durante 10 días, con valor inicial 1000 y guardar los CSV generados en C:\MiDirectorio:

<pre lang="markdown"> python monteCarlo.py --rutaCSV C:\MiDirectorio --numSimulaciones 2 --numDias 10 --valorInicial 1000 --carteraCompleta Sí --nombreCartera Cartera1 </pre>

Si ahora en vez de simular la cartera al completo queremos simular cada una de sus componentes por separado:

<pre lang="markdown"> python monteCarlo.py --rutaCSV C:\MiDirectorio --numSimulaciones 2 --numDias 10 --valorInicial 1000 --carteraCompleta No --nombreCartera Cartera1 </pre>

Si queremos imponer determinadas medias y desviaciones típicas para los retornos de cada uno de los activos, por ejemplo medias 0.1 0.2 y desviaciones típicas 0.07 y 0.05:

<pre lang="markdown"> python monteCarlo.py --rutaCSV C:\MiDirectorio --medias 0.1 0.2 --desviacionesTipicas 0.07 0.05 --numSimulaciones 2 --numDias 10 --valorInicial 1000 --carteraCompleta Sí --nombreCartera Cartera1 </pre>
