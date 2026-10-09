from fastapi import Depends, FastAPI, HTTPException

from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, engine
from models import UserDB, Base, NoteDB, ProductforsaleDB,OrderDB


import bcrypt
import jwt

import os


from datetime import datetime, timedelta, timezone




SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("нет SECRET_KEY")

Base.metadata.create_all(bind=engine)



def create_access_token(user_id:int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes = 60)

    }
    return jwt.encode(payload, SECRET_KEY, algorithm ="HS256")




app = FastAPI()

    

class UserRegister(BaseModel):
    email: str
    password: str

class UserPublic(BaseModel):
    email:str
    id:int

class NoteCreate(BaseModel):
    text: str

class NotePublic(BaseModel):
    text: str
    id: int


class CreateProduct(BaseModel):
    title: str
    price: int


class ProductPublic(BaseModel):
    title: str
    price: int
    id: int



class Orderpublic(BaseModel):
    id: int




def get_current_user(token, db:Session = Depends(get_db)):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Билет потух")      
    user_id = int(payload["sub"])

    user  = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Юзер не найден")      
    return user




@app.post("/auth/register")
def create_account(user_data: UserRegister, db: Session = Depends(get_db)):
    if db.query(UserDB).filter(UserDB.email == user_data.email).first():
        raise HTTPException(status_code=400, detail = "Пользователь уже загестрирован")
    new_account = UserDB(email = user_data.email, password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return {"message": "Вы успешно зарегестрировались"}


@app.get("/auth/me")
def show_my_account(current_user: UserDB = Depends(get_current_user)):
    return UserPublic(id = current_user.id, email = current_user.email)
    




@app.post("/auth/login")
def confirm_registered(user_data: UserRegister, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if user and bcrypt.checkpw(user_data.password.encode('utf-8'), user.password.encode('utf-8')):
        
        token = create_access_token(user.id)
        return {"access_token": token, "token_type": "bearer"}

    else:
        raise HTTPException(status_code=401, detail = "Неверный логин или пароль")




@app.post("/notes")
def Note_Create(note_data: NoteCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not note_data.text.strip():
        raise HTTPException(status_code = 400, detail = "заметка не должна быть пустой")
    

    new_note = NoteDB(text = note_data.text, user_id = current_user.id)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return {"id": new_note.id, "text": note_data.text, "user_id": new_note.user_id}

@app.get("/notes")
def Show_Notes(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    notes_public_list = []

    notes = db.query(NoteDB).filter(NoteDB.user_id == current_user.id).all()
    for note in notes:
        notes_public = NotePublic(text = note.text, id = note.id)

        notes_public_list.append(notes_public)
    return notes_public_list

@app.delete("/notes/{note_id}")
def Delete_Note(note_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
    if note is None:
        raise HTTPException(status_code = 404, detail = "не найдено")
    if note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail = "не найдено юзера такого нах")

    db.delete(note)
    db.commit()
    return {"ok": "True"}




@app.patch("/notes/{note_id}")
def update_note(note_id: int, note_text: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not note_text.strip():
        raise HTTPException(status_code = 400, detail = "нельзя обновить на воздух")
    
    note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
    if note is None:
        raise HTTPException(status_code = 404, detail = "Такой заметки нет")
    if note.user_id != current_user.id:
        raise HTTPException(status_code = 403, detail = "Не твоя заметка")
    note.text = note_text

    db.commit()
    db.refresh(note)
 
    return {"id": note.id, "text": note.text}


@app.get("/notes/{note_id}")
def OpenNotes(note_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    notes = db.query(NoteDB).filter(NoteDB.id == note_id).first()

    if not notes:
        raise HTTPException(status_code = 404, detail = "Такой задачи не найдено/Такой задачи нет")
    
    if notes.user_id != current_user.id:
        raise HTTPException(status_code = 403, detail = "Такой задачи нет в вашем профиле") 

    return {"id": notes.id, "text": notes.text}







@app.post("/products")
def open_product(product_data: CreateProduct, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not product_data.title.strip():
        raise HTTPException(status_code = 400, detail = "поле не должно быть пустым")


    if product_data.price <= 0:
        raise HTTPException(status_code = 400, detail = "цена не должна быть равна 0")

    productforsale = ProductforsaleDB(title = product_data.title, price = product_data.price, user_id = current_user.id) 
    
    db.add(productforsale)
    db.commit()
    db.refresh(productforsale)
    
    return {"id": productforsale.id, "title": productforsale.title, "price": productforsale.price, "user_id": productforsale.user_id}




@app.get("/products")
def ShowProduct(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    productforsale_list = []

    productforsales = db.query(ProductforsaleDB).filter(ProductforsaleDB.user_id == current_user.id).all()
    for productforsale in productforsales:
        productforsale_public = ProductPublic(price = productforsale.price, title = productforsale.title, id = productforsale.id)

        productforsale_list.append(productforsale_public)

    return productforsale_list


@app.delete("/products/{product_id}")
def DeleteProduct(product_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    productfordelete = db.query(ProductforsaleDB).filter(ProductforsaleDB.id == product_id).first()

    if not productfordelete:
        raise HTTPException(status_code = 404, detail = "Такого продукта нет в списке")
    if productfordelete.user_id != current_user.id:
        raise HTTPException(status_code = 403, detail = "Такого продукта нет в вашем профиле")

    db.delete(productfordelete)
    db.commit()
    return {"ok": True}


        
@app.patch("/product/{product_id}")
def UpdateProduct(product_data: CreateProduct, product_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if not product_data.title.strip():
        raise HTTPException(status_code = 400, detail = "нельзя обновить на воздух")
    
    if product_data.price <= 0:
        raise HTTPException(status_code = 400, detail = "нельзя обновить на цену ниже или равную нулю")

    productforupdate = db.query(ProductforsaleDB).filter(ProductforsaleDB.id == product_id).first()


    if not productforupdate:
        raise HTTPException(status_code = 404, detail = "Такого продукта нет в списке")
    if productforupdate.user_id != current_user.id:
        raise HTTPException(status_code = 403, detail = "Такого продукта нет в вашем профиле")

    productforupdate.title = product_data.title
    productforupdate.price = product_data.price

    db.commit()
    return {"id": productforupdate.id, "title": productforupdate.title, "price": productforupdate.price}




@app.get("/product/{product_id}")
def getproudct(product_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    getallproduct = db.query(ProductforsaleDB).filter(ProductforsaleDB.id == product_id).first()
    if not getallproduct:
        raise HTTPException(status_code = 404, detail = "такого продукта нет")

    if getallproduct.user_id != current_user.id:
        raise HTTPException (status_code = 403, detail = "такой задачи нет в твоем профиле")

    
    return {"id": getallproduct.id, "title": getallproduct.title, "price": getallproduct.price}




@app.post("/order")
def open_order(product_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(ProductforsaleDB).filter(ProductforsaleDB.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code = 404, detail = "нет такой штуки здесь")
    if product.user_id == current_user.id:
        raise HTTPException(status_code = 400, detail = "нельзя купить товар, который вы уже купили")
    


    already = db.query(OrderDB).filter(OrderDB.product_id == product.id, OrderDB.user_id == current_user.id).first()
    if already:
        raise HTTPException(status_code = 400, detail = "нельяз купить один товар два раза")
  
    
    new_purchase = OrderDB(product_id=product_id, user_id = current_user.id)

    db.add(new_purchase)
    db.commit()
    db.refresh(new_purchase)
    return {"id": new_purchase.id, "user_id": new_purchase.user_id, "product_id":new_purchase.product_id }


@app.get("/orders")
def show_my_purchases_orders(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    purchases_list = []

    purchases = db.query(OrderDB).filter(OrderDB.user_id == current_user.id).all()

    for my_purchases in purchases:
        purchases_public = Orderpublic(id = my_purchases.id, user_id = my_purchases.user_id, product_id = my_purchases.product_id)

        purchases_list.append(purchases_public)
    return purchases_list


@app.get("/order/{order_id}")
def show_exactly_purchases(order_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(OrderDB).filter(OrderDB.id == order_id).first()

    if not orders:
        raise HTTPException(status_code = 404, detail = "такой строки нет")

    if orders.user_id != current_user.id:
        raise HTTPException(status_code = 403, detail = "Такого ордера нет в списке")

    return {"id": orders.id, "product_id": orders.product_id, "user_id": orders.user_id}



@app.delete("/order/{order_id}")
def delete_order(order_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):

    order_for_delete = db.query(OrderDB).filter(OrderDB.id == order_id).first()

    if not order_for_delete:
        raise HTTPException(status_code = 404, detail = "Такого ордера нет")
    if order_for_delete.user_id != current_user.id:
        raise HTTPException(status_code = 403, detail = "Такой оффер не принадлежит тебе")
    db.delete(order_for_delete)
    db.commit()

    return {"ok": True}




@app.get("/shop")
def show_shop(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    shop_list = []

    open_shop_other_users = db.query(ProductforsaleDB).filter(ProductforsaleDB.user_id != current_user.id).all()

    for shop in open_shop_other_users:
        shopforsalespublic = ProductPublic(id = shop.id, title = shop.title, price = shop.price) 

    
    
        shop_list.append(shopforsalespublic)
    return shop_list

