import streamlit as st
import advertools as adv
import pandas as pd
from urllib.parse import unquote, urlparse
from pathlib import  PurePosixPath
import re
import datetime


#Devuelve el nombre del path de la URL que esté al nivel que le pasemos
def getPathUrl(url,nivel):
    ruta=''
    paths = urlparse(url).path
    partes=PurePosixPath(unquote(paths)).parts
    if nivel < len(partes):
        ruta=partes[nivel]
    return ruta

#Devuelve la fecha que se encuentra en la URL
def getFechaUrl(url):
    fecha=''
    reg_ex=r"^\d\d\d\d$" 
    paths = urlparse(url).path
    partes=PurePosixPath(unquote(paths)).parts
    i=0
    pos=-1
    enc=False
    while i<len(partes) and not enc:
        parte=partes[i]
        rl=re.findall(reg_ex,parte) 
        if len(rl)>0:
            enc=True
            pos=i
        i+=1
    if pos>0:
        fecha=str(partes[pos])+"-"+str(partes[pos+1])+"-"+str(partes[pos+2])
    return fecha

formato_fecha='%Y-%m-%d'
sitemap_url=st.text_input('Ruta del sitemap','')
if len(sitemap_url)>0:
    nivel=st.slider('Nivel del path cuyos datos quedemos agrupar', 1, 5, 2)
    #Pasamos el sitemap a DataFrame
    sitemap_df = adv.sitemap_to_df(sitemap_url)
    #Obtenemos el campo fecha a partir de la URL
    sitemap_df['fecha']=sitemap_df['loc'].apply(getFechaUrl)
    #Obtenemos el campo path a partir de la URL
    sitemap_df['path']=sitemap_df.apply(lambda x: getPathUrl(x['loc'],2), 
                        axis=1)
    #Calculamos los valores agrupados
    df_agrupado=sitemap_df.groupby(['fecha', 'path'],as_index=False).size()
    st.dataframe(df_agrupado)
    st.download_button(
        label="Descargar como CSV",
        data=df_agrupado.to_csv(index=False).encode('utf-8'),
        file_name='people_also_ask.csv',
        mime='text/csv'
        )
    st.subheader('Obtener datos por fechas:')
    inicio= str(st.date_input(
    "Fecha inicial",
    datetime.date(2022, 10, 1)))
    fin=str(st.date_input(
    "Fecha final",
    datetime.date(2022, 10, 1)))

    
    #convertimos la columna fecha al formato adecuado para poder filtrar
    df_agrupado['fecha']=pd.to_datetime(df_agrupado['fecha'], format=formato_fecha)
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
