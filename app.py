import streamlit as st
import advertools as adv
import pandas as pd
from urllib.parse import unquote, urlparse
from pathlib import  PurePosixPath
import re
import datetime

st.set_page_config(
   page_title="Obtener datos de categorías de URL publicadas en sitemap"
)
st.title("Obtener datos de categorías de URL publicadas en sitemap")

#Variedad de formatos de fechas
L_F_FECHAS=['/YYYY/MM/DD/', '/YYYYMMDD/']

#Devuelve el nombre del path de la URL que esté al nivel que le pasemos
def getPathUrl(url,nivel):
    ruta=''
    paths = urlparse(url).path
    partes=PurePosixPath(unquote(paths)).parts
    if nivel < len(partes):
        ruta=partes[nivel]
    return ruta

#Devuelve la fecha que se encuentra en la URL
def getFechaUrl(url,formato_fecha):
    fecha=''
    paths = urlparse(url).path
    partes=PurePosixPath(unquote(paths)).parts
    i=0
    pos=-1
    enc=False
    #Si el formato de fecha es año, mes y día separados en distintos paths
    if formato_fecha==L_F_FECHAS[0]:
        reg_ex=r"^\d\d\d\d$" 
     #Si el formato de fecha es año, mes y día en el mismo path
    else:
         reg_ex=r"^\d\d\d\d\d\d\d\d$" 
    while i<len(partes) and not enc:
        parte=partes[i]
        rl=re.findall(reg_ex,parte) 
        if len(rl)>0:
            enc=True
            pos=i
        i+=1
    if pos>0:
        #Si el formato de fecha es año, mes y día separados en distintos paths
        if formato_fecha==L_F_FECHAS[0]:
            fecha=str(partes[pos])+"-"+str(partes[pos+1])+"-"+str(partes[pos+2])
        #Si el formato de fecha es año, mes y día en el mismo path
        else:
            fecha=str(partes[pos])
    return fecha

#Pasamos el sitemap recibido a DataFrame 
@st.cache
def procesarSitemap(url):
    sitemap_df = adv.sitemap_to_df(url)
    return sitemap_df

#Valida el formato de fecha
def checkFormatoFecha(df,formato):
    ok=False
    #Si el formato de fecha es año, mes y día separados en distintos paths
    if formato==L_F_FECHAS[0]:
        reg_ex="/\d\d\d\d/\d\d/\d\d/" 
     #Si el formato de fecha es año, mes y día en el mismo path
    else:
         reg_ex=r"/\d\d\d\d\d\d\d\d/" 
    cont=0
    cont=df['loc'].str.count(reg_ex).sum()
    if cont>0:
        ok=True
    return ok



#Añadimos columnas con la fecha y la categoría de la quequeremos obtener el volumen de URL publicadas
def addColumnsDataFrame(sitemap_df,f_fecha_url,nivel_cat):
    ok=checkFormatoFecha(sitemap_df,f_fecha_url)
    if ok:
        sitemap_df['fecha']=sitemap_df.apply(lambda x: getFechaUrl(x['loc'],f_fecha_url), 
                        axis=1)
    else:
        st.warning("No ha seleccionado el formato de fecha adecuado")
        sitemap_df['fecha']='Error'
    #Obtenemos el campo path a partir de la URL
    sitemap_df['path']=sitemap_df.apply(lambda x: getPathUrl(x['loc'],nivel_cat), 
                        axis=1)
    return sitemap_df

sitemap_url=st.text_input('Ruta del sitemap','')

if len(sitemap_url)>0:
    #Pasamos el sitemap a DataFrame 
    sitemap_df = procesarSitemap(sitemap_url)

    if sitemap_df is not None:
        st.text("Elementos del sitemap cargado")
        st.dataframe(sitemap_df)
        #formato de fecha en la URL
        f_fecha_url = st.radio(
            'Selecciona el formato de fecha que se muestra en la URL',
            (L_F_FECHAS))
        nivel=st.slider('Profundidad del path que identifica la categoría cuyos datos quedemos agrupar', 1, 5, 2)
        #obtenemos fechas y categorías a agrupar. Lo asignamos a otra variable para evitar mutaciones
        deep_copy = sitemap_df.copy()
        sitemap_nuevo = addColumnsDataFrame(deep_copy,f_fecha_url,nivel)
        
        #Calculamos los valores agrupados
        df_agrupado=sitemap_nuevo.groupby(['fecha', 'path'],as_index=False).size()
        st.dataframe(df_agrupado)
        st.download_button(
            label="Descargar como CSV",
            data=df_agrupado.to_csv(index=False).encode('utf-8'),
            file_name='agrupados.csv',
            mime='text/csv'
            )
        st.subheader('Obtener datos por fechas:')
        inicio= str(st.date_input(
        "Fecha inicial",
        datetime.date(2022, 10, 1)))
        fin=str(st.date_input(
        "Fecha final",
        datetime.date(2022, 10, 1)))

        #Formato de fecha que utilizaremos para filtrar
        FORMATO_FECHA_FILTRO='%Y-%m-%d'
        #convertimos la columna fecha al formato adecuado para poder filtrar
        df_agrupado['fecha']=pd.to_datetime(df_agrupado['fecha'], format=FORMATO_FECHA_FILTRO)
        # Filter data between two dates
        filtered_df = df_agrupado.loc[(df_agrupado['fecha'] >= inicio)
                        & (df_agrupado['fecha'] <= fin)]
        df_final=filtered_df.groupby(['path'],as_index=False).sum()
        st.dataframe(df_final)
        st.download_button(
            label="Descargar como CSV",
            data=df_final.to_csv(index=False).encode('utf-8'),
            file_name=inicio+"_"+fin+'.csv',
            mime='text/csv'
            )
