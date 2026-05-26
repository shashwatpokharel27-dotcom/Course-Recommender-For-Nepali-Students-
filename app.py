from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, computed_field
from typing import Literal, Annotated, List
import pandas as pd
import numpy as np
import joblib, json
import os

# Creating an instance of the FastAPI application
app = FastAPI(title="Nepal Course Recommender Pro", version="1.0")

# SERVE FRONTEND
app.mount("/static", StaticFiles(directory="static"), name="static")

# HOME ROUTE
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hard Filter Database
COURSES_DB = {
    "mbbs": {"stream": ["Science (Bio)"], "min_gpa": 2.4},
    "bpharmacy": {"stream": ["Science (Bio)", "Science (Physical)"], "min_gpa": 2.4},
    "civil engineering": {"stream": ["Science (Physical)", "Technical"], "min_gpa": 2.0},
    "computer engineering": {"stream": ["Science (Physical)", "Technical"], "min_gpa": 2.0},
    "electrical engineering": {"stream": ["Science (Physical)", "Technical"], "min_gpa": 2.0},
    "bsc csit": {"stream": ["Science (Physical)", "Science (Bio)"], "min_gpa": 2.0},
    "bit": {"stream": ["Science (Bio)", "Science (Physical)", "Management", "Humanities", "Law", "Education"], "min_gpa": 2.0},
    "bca": {"stream": ["Science (Bio)", "Science (Physical)", "Management", "Humanities", "Law", "Education", "Technical"], "min_gpa": 2.0},
    "bba": {"stream": ["Management", "Science (Bio)", "Science (Physical)"], "min_gpa": 1.8},
    "bbm": {"stream": ["Management", "Science (Bio)", "Science (Physical)"], "min_gpa": 1.8},
    "bhm": {"stream": ["Management", "Humanities", "Science (Bio)", "Science (Physical)"], "min_gpa": 1.8},
    "bbs": {"stream": ["Management", "Humanities", "Science (Bio)", "Science (Physical)", "Education"], "min_gpa": 1.6}
}

BOOK_DB = {
    "mbbs": [
        ("The Emperor of All Maladies: A Biography of Cancer - by Dr. Siddhartha Mukherjee", "https://cdn.shoplightspeed.com/shops/611345/files/64218503/scribner-the-emperor-of-all-maladies-a-biography-o.jpg"),
        ("When Breath Becomes Air - by Dr. Paul Kalanithi", "https://bookmarksandbluelight.wordpress.com/wp-content/uploads/2018/03/39-when-breath-becomes-air_paul-kalanithi.jpg?w=250&h=388"),
        ("The Immortal Life of Henrietta Lacks - by Rebecca Skloot", "https://imgs.search.brave.com/84SAMlR2GBWLmmfZ7rIYMKftFDnfazQZREOdcoYczKs/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly91cGxv/YWQud2lraW1lZGlh/Lm9yZy93aWtpcGVk/aWEvZW4vNS81Zi9U/aGVfSW1tb3J0YWxf/TGlmZV9IZW5yaWV0/dGFfTGFja3NfJTI4/Y292ZXIlMjkuanBn/P3V0bV9zb3VyY2U9/ZW4ud2lraXBlZGlh/Lm9yZyZ1dG1fY2Ft/cGFpZ249cGFyc2Vy/JnV0bV9jb250ZW50/PXRodW1ibmFpbF91/bnNjYWxlZA"),
        ("BD Chaurasia’s Human Anatomy - by BD Chaurasia", "https://imgs.search.brave.com/dQToUSLp0PkN90XiMrxD0ETNaWS0mtyGHDQOsWbb6ds/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly90aGVh/bmF0b215c2hvcC5j/b20vaW1hZ2UvY2Fj/aGUvY2F0YWxvZy9i/ZF9jaGF1cmFzaWFf/Ym9va18wMi0xMjAw/eDEyMDAuanBn")
    ],
    "bpharmacy": [
        ("Principles of Anatomy & Physiology - by Gerard J. Tortora & Bryan Derrickson", "https://imgs.search.brave.com/DoepOIRxg6Jn92HFayAn4lRgKMxYSZDu-zszH6Cg8lc/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly93d3cu/d2lsZXlwbHVzLmNv/bS93cC1jb250ZW50/L3VwbG9hZHMvMjAy/MC8wOS85NzgxMTE5/NjYyNjg2LVRvcnRv/cmEtUEFQLTE2ZS1D/b3Zlci5qcGc"),
        ("Anatomy and Physiology in Health and Illness - by Kathleen J. W. Wilson & Anne Waugh", "https://imgs.search.brave.com/Wjl1Fo4OodUVi9zOgxmaemeU_d3e8VuVDmTdRMTy2iY/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9jb3Zl/cnMub3BlbmxpYnJh/cnkub3JnL2IvaWQv/MTIzMTU0NS1NLmpw/Zw"),
        ("Pharmaceutics I - by R. M. Mehta", "https://imgs.search.brave.com/dMT5r2w_KjB4X-zWdVJb4J3jUNjzqCDDb_q--1AvLcg/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9nLnNk/bGNkbi5jb20vaW1n/cy9rLzAvMy9QSEFS/TUFDRVVUSUNTLTEt/QlktUi1NLVNETDA1/MzMxNjI2OC0xLTgz/M2M0LmpwZWc_dz0x/MzAmaD0xNTI"),
        ("Organic Chemistry - by Morrison and Boyd", "https://imgs.search.brave.com/qPeEH1Q68r9yKESzjqVD2X95VJHc9qrwmgOUHro0gdE/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9jb3Zl/cnMub3BlbmxpYnJh/cnkub3JnL2IvaWQv/NjU0ODIzNC1MLmpw/Zw")
    ],
    "civil engineering": [
        ("Basic Civil Engineering - by S. S. Bhavikatti", "https://imgs.search.brave.com/-xxyvfo8vBDzYCSAaIwtJ23crhVsgi-YnY7eLOtvZqw/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pbnN0/YXBkZi5pbi93cC1j/b250ZW50L3VwbG9h/ZHMvaW1nLzIwMjAv/MDcvYmFzaWMtY2l2/aWwtZW5naW5lZXJp/bmctYnktc3MtYmhh/dmlrYXR0aS53ZWJw"),
        ("Higher Engineering Mathematics - by B. S. Grewal", "https://imgs.search.brave.com/kup5eVScgUHPXw2syph_-F5lY90iPQzmNHW2QKHYYq4/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pbWFn/ZS5zbGlkZXNoYXJl/Y2RuLmNvbS9ncmV3/YWxiLTE2MDkwNzEz/NTA0MC84NS9ISUdI/RVItRU5HSU5FRVJJ/TkctTUFUSEVNQVRJ/Q1MtYnktQi1TLUdS/RVdBTC0xLTMyMC5q/cGc"),
        ("Engineering Mechanics - by S. Timoshenko & D. H. Young", "https://imgs.search.brave.com/8k7F6ypinVnL9CezL0YPoVUW6-6lLkagpq14EXSiwBQ/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9wcmFn/YXRpb25saW5lLmNv/bS93cC1jb250ZW50/L3VwbG9hZHMvMjAy/MS8wNC9FTkdJTkVF/UklORy1NRUNIQU5J/Q1MtUy4tVElNT1NI/RU5LTy1ELi1ILi1Z/T1VORy1KLi1WLi1S/QU8tU1VLVU1BUi1Q/QVRJLmpwZw"),
        ("Engineering Drawing - by N. D. Bhatt", "https://imgs.search.brave.com/CUnYJS_xirbRJ5M2iE-nLblQ-S5eFjTHISSQVMPsBS8/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly93d3cu/c2Nob29sY2hhbXAu/bmV0L2ltYWdlL2Nh/Y2hlL2NhdGFsb2cv/Y29sbGVnZS9iZW5n/Zy9lbmdpbmVlcmlu/Zy1kcmF3aW5nLWJ5/LW4tZC1iaGF0dC1s/YXRlc3QtZWRpdGlv/bi00NjJ4NTIxLndl/YnA")
    ],
    "computer engineering": [
        ("The C Programming Language - by Brian W. Kernighan & Dennis M. Ritchie", "https://imgs.search.brave.com/czwWiaR4JsQeoWwS_Sx3fRwGCzCMfVc5yrjc0urahoI/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9tLm1l/ZGlhLWFtYXpvbi5j/b20vaW1hZ2VzL0kv/NDErLXJ2dnJjYkwu/anBn"),
        ("Higher Engineering Mathematics - by B. S. Grewal", "https://imgs.search.brave.com/kup5eVScgUHPXw2syph_-F5lY90iPQzmNHW2QKHYYq4/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pbWFn/ZS5zbGlkZXNoYXJl/Y2RuLmNvbS9ncmV3/YWxiLTE2MDkwNzEz/NTA0MC84NS9ISUdI/RVItRU5HSU5FRVJJ/TkctTUFUSEVNQVRJ/Q1MtYnktQi1TLUdS/RVdBTC0xLTMyMC5q/cGc"),
        ("Computer Fundamentals - by P. K. Sinha & Priti Sinha", "https://bpbonline.com/cdn/shop/products/1058_Epub.jpg?v=1755670156&width=493"),
        ("Code: The Hidden Language of Computer Hardware and Software - by Charles Petzold", "https://www.oreilly.com/covers/urn:orm:book:9780137909261/296w/?format=webp")
    ],
    "electrical engineering": [
        ("Basic Electrical Engineering - by V. K. Mehta & Rohit Mehta", "https://imgs.search.brave.com/TylXPSdVPte5iIJpKWu18VhpOF5ezX5eeQDJGsKtf1E/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9lbGVj/dHJpY2FsY29ubmVj/dHMuY29tL2Zyb250/ZW5kL2ltYWdlcy9m/cmVlX2l0ZW1zL2lt/YWdlLTIwMjEtMDUt/MDgtMTcwNDI1Lndl/YnA"),
        ("Higher Engineering Mathematics - by B. S. Grewal", "https://imgs.search.brave.com/kup5eVScgUHPXw2syph_-F5lY90iPQzmNHW2QKHYYq4/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pbWFn/ZS5zbGlkZXNoYXJl/Y2RuLmNvbS9ncmV3/YWxiLTE2MDkwNzEz/NTA0MC84NS9ISUdI/RVItRU5HSU5FRVJJ/TkctTUFUSEVNQVRJ/Q1MtYnktQi1TLUdS/RVdBTC0xLTMyMC5q/cGc"),
        ("Electrical Engineering 101 - by Darren Ashby", "https://imgs.search.brave.com/7qtQpdf96CHeC-FfuSf6Nq3qwpP3FoDTTKf-fsUWI8o/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pbWFn/ZS5lYm9va3MuY29t/L2NvdmVyLzQxMzg2/OS5qcGc_d2lkdGg9/MjEwJmhlaWdodD0z/MTUmcXVhbGl0eT04/NQ"),
        ("Engineering Circuit Analysis - by William H. Hayt & Jack E. Kemmerly", "https://imgs.search.brave.com/oJPKFUjerVFH1B1kuBIgMlz6u6seWGxRpRb2RG7XQP0/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9ibG9n/Z2VyLmdvb2dsZXVz/ZXJjb250ZW50LmNv/bS9pbWcvYi9SMjl2/WjJ4bC9BVnZYc0Vq/SE1ZeGRDTjVFSUhB/eE1EcjNJOGs1TDVU/S2ZPc3lka0NUblky/aEdLUVR5UmoyenZH/ZDBfa1I2M29iYVdK/OHFtNndSUGJ3bWtL/QXpnY0FraldiX1ZK/eFV4dVpDazAzd3ZF/R3ZJWUNkNl9xWGdJ/cmZNQnRsZEpQQTZB/b3lMUHVkNG1hRkFk/YmpwTXhsdk0vczY0/MC9FbmdpbmVlcmlu/ZytDaXJjdWl0K0Fu/YWx5c2lzKytieStX/aWxsaWFtK0guK0hh/eXQrJTJDK0phY2sr/S2VtbWVybHkrJTJD/K1N0ZXZlbitNLitE/dXJiaW4uanBn")
    ],
    "bsc csit": [
        ("The C Programming Language - by Brian W. Kernighan & Dennis M. Ritchie", "https://imgs.search.brave.com/5686vAQ7LUhZTURWJwf0q-8sHgmYnUabSyJTfufOCrs/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pLmVi/YXlpbWcuY29tL2lt/YWdlcy9nL21qQUFB/ZVN3N1Q1cUItYncv/cy1sMjI1LmpwZw"),
        ("Computer Fundamentals - by P. K. Sinha & Priti Sinha", "https://imgs.search.brave.com/HY5oOSkQ2bRdWl4XQQewiYcsMC7uou5W9znNqO9czIg/rs:fit:200:200:1:0/g:ce/aHR0cHM6Ly9icGJv/bmxpbmUuY29tL2Nk/bi9zaG9wL3Byb2R1/Y3RzLzEwNThfRXB1/Yi5qcGc_dj0xNzU1/NjcwMTU2JndpZHRo/PTE5MjA"),
        ("Higher Engineering Mathematics - by B. S. Grewal", "https://imgs.search.brave.com/kup5eVScgUHPXw2syph_-F5lY90iPQzmNHW2QKHYYq4/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pbWFn/ZS5zbGlkZXNoYXJl/Y2RuLmNvbS9ncmV3/YWxiLTE2MDkwNzEz/NTA0MC84NS9ISUdI/RVItRU5HSU5FRVJJ/TkctTUFUSEVNQVRJ/Q1MtYnktQi1TLUdS/RVdBTC0xLTMyMC5q/cGc"),
        ("Computer Networking: A Top-Down Approach - by James F. Kurose & Keith W. Ross", "https://imgs.search.brave.com/L9auTU0U8VRiY9rGnfl3CztUG2zifTd4pPON5LPSVUo/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9waWN0/dXJlcy5hYmVib29r/cy5jb20vaXNibi85/NzgwMTMxMzY1NDgz/LXVzLTMwMC5qcGc")
    ],
    "bit": [
        ("The C Programming Language - by Brian W. Kernighan & Dennis M. Ritchie", "https://imgs.search.brave.com/5686vAQ7LUhZTURWJwf0q-8sHgmYnUabSyJTfufOCrs/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pLmVi/YXlpbWcuY29tL2lt/YWdlcy9nL21qQUFB/ZVN3N1Q1cUItYncv/cy1sMjI1LmpwZw"),
        ("Computer Fundamentals - by P. K. Sinha & Priti Sinha", "https://imgs.search.brave.com/HY5oOSkQ2bRdWl4XQQewiYcsMC7uou5W9znNqO9czIg/rs:fit:200:200:1:0/g:ce/aHR0cHM6Ly9icGJv/bmxpbmUuY29tL2Nk/bi9zaG9wL3Byb2R1/Y3RzLzEwNThfRXB1/Yi5qcGc_dj0xNzU1/NjcwMTU2JndpZHRo/PTE5MjA"),
        ("Higher Engineering Mathematics - by B. S. Grewal", "https://imgs.search.brave.com/kup5eVScgUHPXw2syph_-F5lY90iPQzmNHW2QKHYYq4/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pbWFn/ZS5zbGlkZXNoYXJl/Y2RuLmNvbS9ncmV3/YWxiLTE2MDkwNzEz/NTA0MC84NS9ISUdI/RVItRU5HSU5FRVJJ/TkctTUFUSEVNQVRJ/Q1MtYnktQi1TLUdS/RVdBTC0xLTMyMC5q/cGc"),
        ("Database System Concepts - by Abraham Silberschatz, Henry F. Korth & S. Sudarshan", "https://imgs.search.brave.com/m8_YeLQNPHK4bfkYJCdklSW-z3fdnFy8MXOM-sSW4b4/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pbWFn/ZS5zbGlkZXNoYXJl/Y2RuLmNvbS9kYXRh/YmFzZS1zeXN0ZW0t/Y29uY2VwdHMtN25i/c3BlZC0xMjYwMDg0/NTA3LTk3ODEyNjAw/ODQ1MDRjb21wcmVz/cy0yMjA1MjAxNjM2/MDUtMjRjOTQyYjUv/ODUvZGF0YWJhc2Ut/c3lzdGVtLWNvbmNl/cHRzLTduYnNwZWQt/MTI2MDA4NDUwNy05/NzgxMjYwMDg0NTA0/X2NvbXByZXNzLXBk/Zi0xLTMyMC5qcGc")
    ],
    "bca": [
        ("Programming in ANSI C - by E. Balagurusamy", "https://www.mheducation.co.in/media/catalog/product/cache/081b8c22b4dd107671c14f517fd777a1/9/7/9789355326720.jpeg"),
        ("Computer Fundamentals - by P. K. Sinha & Priti Sinha", "https://imgs.search.brave.com/HY5oOSkQ2bRdWl4XQQewiYcsMC7uou5W9znNqO9czIg/rs:fit:200:200:1:0/g:ce/aHR0cHM6Ly9icGJv/bmxpbmUuY29tL2Nk/bi9zaG9wL3Byb2R1/Y3RzLzEwNThfRXB1/Yi5qcGc_dj0xNzU1/NjcwMTU2JndpZHRo/PTE5MjA"),
        ("Higher Engineering Mathematics - by B. S. Grewal", "https://imgs.search.brave.com/kup5eVScgUHPXw2syph_-F5lY90iPQzmNHW2QKHYYq4/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pbWFn/ZS5zbGlkZXNoYXJl/Y2RuLmNvbS9ncmV3/YWxiLTE2MDkwNzEz/NTA0MC84NS9ISUdI/RVItRU5HSU5FRVJJ/TkctTUFUSEVNQVRJ/Q1MtYnktQi1TLUdS/RVdBTC0xLTMyMC5q/cGc"),
        ("Data Structures Using C - by Reema Thareja", "https://imgs.search.brave.com/JOOa5Uw59gp5bDHP34SB7OY49BoSDPLBidb3WaAQgCU/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pLmVi/YXlpbWcuY29tL2lt/YWdlcy9nL2tOY0FB/T1N3UVZKbDZCY1Uv/cy1sNTAwLndlYnA")
    ],
    "bba": [
        ("Principles of Management - by Stephen P. Robbins & Mary Coulter", "https://imgs.search.brave.com/xF2eN4L4WzbpLYkMJO5i7jEW7qdcS3oFsPl4iFIfxDU/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pLmVi/YXlpbWcuY29tL2lt/YWdlcy9nL2szb0FB/T1N3bzROak9BQ2kv/cy1sNTAwLmpwZw"),
        ("Business Mathematics - by Dr. Sancheti & V. K. Kapoor", "https://imgs.search.brave.com/8ViiS7CwbgsEOy1Br8KfnpzVCohY15jVnpd4-EvK47k/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9ydWtt/aW5pbTIuZmxpeGNh/cnQuY29tL2ltYWdl/LzgwMC84MDAvcmVn/aW9uYWxib29rcy9u/L3cvZS9idXNpbmVz/cy1tYXRoZW1hdGlj/cy1vcmlnaW5hbC1p/bWFla240ZXBqcHp0/eGpkLmpwZWc_cT05/MA"),
        ("Business Communication Today - by Bovee & Thill", "https://imgs.search.brave.com/Rwi2mpleSMeqBpcsA-a3TYVWCW2hWD73vT0EN93bxGI/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pLmVi/YXlpbWcuY29tL2lt/YWdlcy9nL1hXOEFB/T1N3SnJwWmNma0Mv/cy1sNTAwLmpwZw"),
        ("Rich Dad Poor Dad - by Robert T. Kiyosaki", "https://imgs.search.brave.com/PduPqqCNimtjR1QEswWJRZKLrA_DAhDtnHl0IB2nh3Y/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9tZWRp/YS5iZWVoaWl2LmNv/bS9jZG4tY2dpL2lt/YWdlL2ZpdD1zY2Fs/ZS1kb3duLHF1YWxp/dHk9ODAsZm9ybWF0/PWF1dG8sb25lcnJv/cj1yZWRpcmVjdC91/cGxvYWRzL2Fzc2V0/L2ZpbGUvZmU3ZDc3/ZDEtMmFjOS00ZjE5/LWE0ZTMtZGZmZTA2/ZDBmZWZlL2ltYWdl/LnBuZw")
    ],
    "bbm": [
        ("Principles of Management - by Stephen P. Robbins & Mary Coulter", "https://imgs.search.brave.com/xF2eN4L4WzbpLYkMJO5i7jEW7qdcS3oFsPl4iFIfxDU/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pLmVi/YXlpbWcuY29tL2lt/YWdlcy9nL2szb0FB/T1N3bzROak9BQ2kv/cy1sNTAwLmpwZw"),
        ("Financial Accounting - by T. S. Grewal", "https://imgs.search.brave.com/XSz_ovooxPdgQp8Vf3GyEK4nUhf2pzjFFu1-hH5sVNo/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9waWN0/dXJlcy5hYmVib29r/cy5jb20vaXNibi85/Nzg5MzkwODUxMTY0/LXVzLmpwZw"),
        ("Business Mathematics - by Dr. Sancheti & V. K. Kapoor", "https://imgs.search.brave.com/8ViiS7CwbgsEOy1Br8KfnpzVCohY15jVnpd4-EvK47k/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9ydWtt/aW5pbTIuZmxpeGNh/cnQuY29tL2ltYWdl/LzgwMC84MDAvcmVn/aW9uYWxib29rcy9u/L3cvZS9idXNpbmVz/cy1tYXRoZW1hdGlj/cy1vcmlnaW5hbC1p/bWFla240ZXBqcHp0/eGpkLmpwZWc_cT05/MA"),
        ("Microeconomics - by Ahuja", "https://imgs.search.brave.com/DWNDNUvqDHkvrmnt7suoo8nnjMYotn1UKEC3RFbMnnw/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly93aXNo/YWxsYm9vay5jb20v/d3AtY29udGVudC91/cGxvYWRzLzIwMjAv/MDkvV2hhdHNBcHAt/SW1hZ2UtMjAyMC0w/OS0wOS1hdC02LjE4/LjI1LVBNLmpwZWc")
    ],
    "bhm": [
        ("Principles of Management - by Stephen P. Robbins & Mary Coulter", "https://imgs.search.brave.com/xF2eN4L4WzbpLYkMJO5i7jEW7qdcS3oFsPl4iFIfxDU/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pLmVi/YXlpbWcuY29tL2lt/YWdlcy9nL2szb0FB/T1N3bzROak9BQ2kv/cy1sNTAwLmpwZw"),
        ("Professional Food and Beverage Service - by Dennis R. Lillicrap & John A. Cousins", "https://imgs.search.brave.com/NCsI_-Rh1VSfhIQjb7AB2MhPFs2KTwLpogGNljXiDAw/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9waWN0/dXJlcy5hYmVib29r/cy5jb20vaXNibi85/NzgwMzQwODQ3MDIy/LXVrLTMwMC5qcGc"),
        ("Theory of Cookery - by K. Arora", "https://imgs.search.brave.com/AUmSKbygN55ubHaRS6-9z_SXkg8OLKF4kYQwdOsNHz0/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9pbWFn/ZXMubWVlc2hvLmNv/bS9pbWFnZXMvcHJv/ZHVjdHMvNDAwMTc4/NjA1L2lhcWo0XzEy/OC53ZWJwP3dpZHRo/PTEyOA"),
        ("Business Communication Today - by Bovee & Thill", "https://imgs.search.brave.com/NkZg15edXbDwlzLu7tcKAvQwrSaAHKalqpQAmxclmdk/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pLmVi/YXlpbWcuY29tL2lt/YWdlcy9nL2VMTUFB/ZVN3b1lScFNHV0cv/cy1sNTAwLmpwZw")
    ],
    "bbs": [
        ("Principles of Management - by Stephen P. Robbins & Mary Coulter", "https://imgs.search.brave.com/xF2eN4L4WzbpLYkMJO5i7jEW7qdcS3oFsPl4iFIfxDU/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pLmVi/YXlpbWcuY29tL2lt/YWdlcy9nL2szb0FB/T1N3bzROak9BQ2kv/cy1sNTAwLmpwZw"),
        ("Financial Accounting - by T. S. Grewal", "https://imgs.search.brave.com/XSz_ovooxPdgQp8Vf3GyEK4nUhf2pzjFFu1-hH5sVNo/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9waWN0/dXJlcy5hYmVib29r/cy5jb20vaXNibi85/Nzg5MzkwODUxMTY0/LXVzLmpwZw"),
        ("Business Economics - by H. L. Ahuja", "https://imgs.search.brave.com/vQSqk66IZHEcT5QzXTkEOjbYBuPlrwzHgaRoA5zFRHU/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9wcmFn/YXRpb25saW5lLmNv/bS93cC1jb250ZW50/L3VwbG9hZHMvMjAy/MS8wNC9CVVNJTkVT/Uy1FQ09OT01JQ1Mt/SC4tTC4tQUhVSkEt/Mi5qcGc"),
        ("Business Mathematics and Statistics - by Sancheti & Kapoor", "https://imgs.search.brave.com/NILhSxxwllV8V8uD3QHONRNXA_BM2j9c0gYhfbes0ak/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9ydWtt/aW5pbTIuZmxpeGNh/cnQuY29tL2ltYWdl/LzgwMC84MDAvcmVn/aW9uYWxib29rcy9u/L3cvZS9idXNpbmVz/cy1tYXRoZW1hdGlj/cy1vcmlnaW5hbC1p/bWFla240bWFhdDVn/bWhtLmpwZWc_cT05/MA")
    ]
}
# Loading saved ML model
try:
    pipeline = joblib.load('Model_Training/course_recommender_Rf.pkl')
    le = joblib.load('Model_Training/label_encoder.pkl')
    model_loaded = True
except FileNotFoundError:
    model_loaded = False
    print("Warning: ML models not found in root. Check file names!")

# Creating pydantic model
class StudentRequest(BaseModel):
    stream: Annotated[Literal['Science (Bio)', 'Science (Physical)', 'Management', 'Humanities', 'Law', 'Education', 'Technical'], Field(..., description="The +2 stream completed by the student")]
    gpa: Annotated[float, Field(..., ge=0.8, le=4.0, description="Overall GPA")]
    interest: str
    career_goal: str
    skills: str
    budget_amount: int

    @computed_field
    @property
    def eligible_courses(self) -> List[str]:
        eligible = []
        for course, criteria in COURSES_DB.items():
            if self.stream in criteria["stream"] and self.gpa >= criteria["min_gpa"]:
                eligible.append(course)
        return eligible

    @computed_field
    @property
    def ml_budget_tier(self) -> str:
        if self.budget_amount >= 1000000: return "High"
        elif self.budget_amount >= 500000: return "Mid"
        else: return "Low"

# Helper to fetch books from Dictionary
def get_books_from_dict(course_name: str):
    # Fetch from dictionary or return empty list if course not found
    books = BOOK_DB.get(course_name.lower(), [])
    return [{"title": title, "image": url} for title, url in books]

@app.post("/predict")
def predict_course(data: StudentRequest):
    eligible_list = data.eligible_courses
    if not eligible_list:
        raise HTTPException(status_code=400, detail="You do not meet the minimum requirements for the listed courses.")

    combined_text = f"{data.interest} {data.career_goal} {data.skills}".lower().strip()
    input_df = pd.DataFrame([{'combined_text': combined_text, 'Budget': data.ml_budget_tier}])

    raw_scores = {}
    if model_loaded:
        probs = pipeline.predict_proba(input_df)[0]
        for i, probability in enumerate(probs):
            course_name = le.inverse_transform([i])[0].lower()
            raw_scores[course_name] = probability
    else:
        raw_scores = {course: 0.5 for course in COURSES_DB.keys()}

    final_recommendations = []
    for course in eligible_list:
        score = raw_scores.get(course, 0)
        # Fetch books from the dictionary helper
        books = get_books_from_dict(course)
        final_recommendations.append({
            "course": course.upper(), 
            "confidence": round(score * 100, 2),
            "books": books
        })

    final_recommendations = sorted(final_recommendations, key=lambda x: x["confidence"], reverse=True)

    return {"student_stream": data.stream, "recommendations": final_recommendations[:3]}

@app.get("/suggestions")
async def get_suggestions():
    try:
        with open('Model_Training/suggestions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError: 
        return {"error": "Suggestions file not found. Run your export script."}

@app.get("/books")
async def read_books():
    return FileResponse('static/books.html')