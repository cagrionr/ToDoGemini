import markdown
from bs4 import BeautifulSoup
from fastapi import APIRouter, Request,Depends, Path, HTTPException
from pydantic import BaseModel, Field
from starlette import status
from starlette.responses import RedirectResponse

from models import Base, Todo
from database import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from Routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import google.generativeai as genai
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage,AIMessage



router=APIRouter(
    prefix="/todo",
    tags=["Todo"]
)




class TodoRequest(BaseModel):
    title: str=Field(min_length=3,max_length=50)
    description:str= Field(min_length=3, max_length=1000)
    priority:int=Field(gt=0,ls=6)
    complete:bool




templates=Jinja2Templates(directory="templates")

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
db_dependency=Annotated[Session, Depends(get_db)]
user_dependency=Annotated[dict,Depends(get_current_user)]

def redirect_to_login():
    redirect_response=RedirectResponse(url="auth/login_page",status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("auth_token")
    return redirect_response




@router.get("/todo-page")
async def render_todo_page(request:Request,db:db_dependency):
    try:
        user= await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todos=db.query(Todo).filter(user.get("user_id")==Todo.owner_id).all()

        return templates.TemplateResponse("todo.html",{"request":request,"todos":todos,"user":user})
    except:
        return redirect_to_login()


@router.get("/add-todo-page")
async def render_add_todo_page(request:Request):
    try:
        user= await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()

        return templates.TemplateResponse("add-todo.html",{"request":request,"user":user})
    except:
        return redirect_to_login()


@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request:Request,todo_id:int,db:db_dependency):
    try:
        user= await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todo=db.query(Todo).filter(Todo.id==todo_id).first()
        return templates.TemplateResponse("edit-todo.html",{"request":request,"todo":todo,"user":user})
    except:
        return redirect_to_login()


@router.get("/")
async def read_all(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(Todo).filter(user.get("user_id")==Todo.owner_id).all()

@router.get("/todo/{todo_id}",status_code=status.HTTP_200_OK)
async def read_by_id(user:user_dependency,db:db_dependency,todo_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo=db.query(Todo).filter(Todo.id==todo_id).filter(Todo.owner_id==user.get("user_id")).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="todo not found")


@router.post("/todo",status_code=status.HTTP_201_CREATED)
async def create_todo(user:user_dependency,db:db_dependency,todo_request:TodoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo=Todo(**todo_request.dict(),owner_id=user.get("user_id"))
    todo.description=(create_todo_with_gemini(todo_request.description))
    db.add(todo)
    db.commit()

@router.put("/todo/{todo_id}",status_code=status.HTTP_200_OK)
async def update_todo(user:user_dependency,db:db_dependency, todo_request:TodoRequest,todo_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo=db.query(Todo).filter(Todo.id==todo_id).filter(Todo.owner_id==user.get("user_id")).first()
    if todo==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    todo.title=todo_request.title
    todo.description=todo_request.description
    todo.priority=todo_request.priority
    todo.complete=todo_request.complete

    db.add(todo)
    db.commit()

@router.delete("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user:user_dependency,db:db_dependency, todo_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo=db.query(Todo).filter(Todo.id==todo_id).filter(Todo.owner_id==user.get("user_id")).first()
    if todo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    db.delete(todo)
    db.commit()


def markdown_text(markdown_string:str):
    html=markdown.markdown(markdown_string)
    soup=BeautifulSoup(html,"html.parser")
    text=soup.get_text()
    return text

def create_todo_with_gemini(todo_string:str):
    load_dotenv()
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm= ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    response=llm.invoke(

        [HumanMessage("I will provide you a todo item to add my to do list. What i want you to do is to create a longer and more comprehensive description of that todo item, my next message will be my todo:"),
            HumanMessage(todo_string)])
    return markdown_text(response.content)

"""

def create_todo_with_gemini(todo_string:str):
    load_dotenv()
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm= ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    response=llm.invoke(

        [HumanMessage("Adıyaman'lı birisi gibi konuş."),
            HumanMessage(todo_string)])
    return response.content
    
    if __name__=="__main__":
    message="Bizim memleket çok güzel."
    print(create_todo_with_gemini(message))
    
    
    Hele gardaş, hoş geldin, sefa geldin! Bizim Adıyaman'ı mı soruyorsun? Vallahi billahi, bizim memleket öyle bir güzel ki, anlatmakla bitmez, kelimeler yetmez.

Şimdi bak, Nemrut Dağı'mız var bir kere. Güneşin doğuşu batışı orada, insanı başka diyarlara götürür. O heykeller, o tarih... İnsanın tüyleri diken diken olur. Sanki zaman durur orada, geçmişle geleceği bir arada yaşarsın.

Bir de Fırat'ın bereketi var. Yeşilliğimiz, toprağımızın verimi... Havası desen, mis gibi. Atatürk Barajı'nın o maviliği, genişliği de cabası. Gözün nereye baksa huzur bulur, gönlün ferahlar.

Ama en güzeli ne biliyor musun? İnsanı gardaş! Misafirperverliğimiz, sıcakkanlılığımız... Kapımız herkese açık, soframız bereketli olur. Kim gelirse başımızın üstünde yeri var. Bir çayımızı iç, bir çiğ köftemizin tadına bak, o zaman anlarsın ne demek istediğimi.

Burası bir başka ya. Huzuru da var, bereketi de, tarihin kokusu da... Her köşesi ayrı bir hikaye anlatır. Gelin, görün hele! Kurban olayım Adıyaman'ıma. Başka yerde bu güzellik zor bulunur. Yav, gel sen de bir gör!

"""
if __name__=="__main__":
    message="Python öğrenmem gerekli. LM/veri bilimi"
    print(create_todo_with_gemini(message))

"""def markdown_text(markdown_string:str):
    html=markdown.markdown(markdown_string)
    soup=BeautifulSoup(html,"html.parser")
    text=soup.get_Text(soup)
    return text

def create_todo_with_gemini(todo_string:str):
    load_dotenv()
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm= ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    response=llm.invoke(

        [HumanMessage("I will provide you a todo item to add my to do list. What i want you to do is to create a longer and more comprehensive description of that todo item, my next message will be my todo:"),
            HumanMessage(todo_string)])
    return markdown_text(response.content)
    if __name__=="__main__":
    message="Python öğrenmem gerekli. LM/veri bilimi"
    print(create_todo_with_gemini(message))


Harika! Gönderdiğin "yapılacak" maddesini daha uzun ve kapsamlı bir açıklama haline getireceğim.
İşte açıklaman:

Yapılacak Madde Açıklaması:
Python Programlama Dili Yetkinliği Kazanımı (Dil Modelleri ve Veri Bilimi Odaklı)
Bu madde, Python programlama dilini temelden ileri düzeye kadar öğrenme ve bu bilgiyi özellikle yapay zeka alanındaki dil modelleri (LM) ile veri bilimi projelerinde etkin bir şekilde uygulama yeteneğini kazanmayı hedeflemektedir.
Detaylı Amaç ve Kapsam:

Temel Python Bilgisi: Dilin sözdizimi, veri yapıları (listeler, sözlükler, kümeler), kontrol akışları (if/else, döngüler), fonksiyonlar, nesne yönelimli programlama (OOP) prensipleri ve hata ayıklama teknikleri gibi temel kavramları sağlam bir şekilde öğrenmek.
Veri Manipülasyonu ve Analizi: NumPy kütüphanesi ile sayısal işlemler ve çok boyutlu dizilerde etkin çalışma; Pandas kütüphanesi ile veri çerçeveleri (DataFrames) kullanarak veri temizleme, dönüştürme, birleştirme ve analiz etme becerilerini geliştirmek.
Veri Görselleştirme: Matplotlib ve Seaborn kütüphaneleri aracılığıyla verileri anlaşılır ve etkili grafikler (histogramlar, dağılım grafikleri, çizgi grafikleri vb.) şeklinde görselleştirmeyi öğrenmek.
Makine Öğrenimi Temelleri: Scikit-learn gibi kütüphaneler kullanarak temel makine öğrenimi algoritmalarını (lineer regresyon, lojistik regresyon, karar ağaçları, kümeleme vb.) anlama, uygulama, model değerlendirme ve hiperparametre optimizasyonu konularında bilgi edinmek.
Doğal Dil İşleme (NLP) ve Dil Modelleri: NLTK, SpaCy gibi kütüphanelerle metin verilerini işleme (tokenizasyon, kök bulma, lemmalama, durak kelimeleri kaldırma), metin sınıflandırma, duygu analizi gibi temel NLP görevlerini gerçekleştirmeyi öğrenmek. Ayrıca, modern dil modellerinin (LLM'ler) çalışma prensipleri, Hugging Face Transformers kütüphanesi gibi araçlarla bu modelleri kullanma ve ince ayar (fine-tuning) yapma konularına giriş yapmak.
Gerçek Dünya Uygulamaları: Öğrenilen teorik bilgileri pratik projelerle pekiştirmek. Kaggle gibi platformlardaki veri setleri üzerinde çalışarak veya kişisel projeler geliştirerek veri bilimi ve dil modelleri alanındaki problem çözme yeteneğini artırmak.

Beklenen Çıktı:
Bu öğrenim sürecinin sonunda, karmaşık veri setlerini Python kullanarak analiz edebilen, çeşitli makine öğrenimi modelleri geliştirebilen ve özellikle doğal dil işleme ile dil modelleri alanında projeler üretebilen bir yetkinliğe ulaşmak hedeflenmektedir. Bu yetkinlik, kariyer gelişimine ve ilgili alandaki projelere anlamlı katkılar sağlamaya olanak tanıyacaktır.


    
    
    """



