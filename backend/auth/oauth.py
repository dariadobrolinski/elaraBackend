from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from auth.jwttoken import verifyToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def getCurrentUser(token: str = Depends(oauth2_scheme)):
    credentialsException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    return verifyToken(token, credentialsException)