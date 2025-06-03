from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

load_dotenv()

def createAccessToken(data: dict):
    toEncode = data.copy()
    # Use UTC time instead of local time
    expire = datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("EXPIRE_MINUTES", "30")))
    toEncode.update({"exp": expire})
    encodedJWT = jwt.encode(toEncode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
    print(f"Created token for user: {data.get('sub')}")
    print(f"Token expires at: {expire}")  # Debug to see expiration time
    return encodedJWT

def verifyToken(token: str, credentialsException):
    try:
        print(f"Verifying token: {token[:20]}...")
        # Decode with UTC time
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        print(f"Token payload: {payload}")
        print(f"Current UTC time: {datetime.now(timezone.utc)}")  # Debug
        username: str = payload.get("sub")
        
        if username is None:
            print("Username is None in payload")
            raise credentialsException
            
        from app import TokenData
        tokenData = TokenData(username=username)
        print(f"Token verified for user: {username}")
        return tokenData

    except JWTError as e:
        print(f"JWT Error: {e}")
        raise credentialsException
    except Exception as e:
        print(f"Other error in verifyToken: {e}")
        raise credentialsException