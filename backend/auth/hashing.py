from passlib.context import CryptContext

pwdCxt = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Hash:
    def bcrypt(password: str):
        return pwdCxt.hash(password)
    def verify(hased, normal):
        return pwdCxt.verify(normal, hased)