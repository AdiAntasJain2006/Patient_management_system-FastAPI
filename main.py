from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Literal, Annotated, Optional
import json
import os
from pathlib import Path as FP

print("Current Working Directory:", os.getcwd())

app = FastAPI()

class patient(BaseModel) :
    id : Annotated[str, Field(..., description="ID of the patient", example='P001')]
    name : Annotated[str, Field(..., description="Name of the patient", example="Prasad patil")]
    city : Annotated[str, Field(..., description="City of the patient", example="Pune")]
    age : Annotated[int, Field(..., description="Age of the patient", example=25)]
    gender : Annotated[Literal["Male", "Female", "Other"], Field(...)]
    height : Annotated[float, Field(..., description="Height of the patient in meters", example=1.75)]
    weight : Annotated[float, Field(..., description="Weight of the patient in kilograms", example=70.5)]
    
    @computed_field
    @property
    def bmi(self) -> float:
        return self.weight / (self.height ** 2)
    
    @computed_field
    @property
    def verdict(self) -> str:
        bmi_value = self.bmi
        if bmi_value < 18.5:
            return "Underweight"
        elif 18.5 <= bmi_value < 24.9:
            return "Normal weight"
        elif 25 <= bmi_value < 29.9:
            return "Overweight"
        else:
            return "Obesity"

def ext_data():
    try:
        path = FP("data.json").resolve()
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="data.json not found"
        )
        
def save_data(data) : 
    path = FP("data.json").resolve()
    with open(path, "w") as f:
        json.dump(data, f)
        
for route in app.routes:
    print(route.path)

@app.get("/")
def read() :
    return {"message": "Hello World"}

@app.get("/about")
def about() :
    return  {"Name" : "Adi Antas Jain"}

@app.get("/data")
def data() :
    return ext_data()

@app.get("/new/{key}")
def data_key(key : str = Path(..., description="Patient id to retrieve from data.json", example="P001"), order : str = Query(..., description="Order of the data (asc or desc)", example="asc")) :
    data = ext_data()
    if key in data:
        return {key : data[key]}
    else : 
        raise HTTPException(status_code=404, detail="Key not found in data.json")
    
@app.post("/create")
def create_patient(patient: patient):
    data = ext_data()
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient already exists")
    data[patient.id] = patient.model_dump(exclude = ['id']) # converts the patient object to a dictionary and excludes the 'id' field
    save_data(data)
    return JSONResponse(status_code=201, content={"message": "Patient created successfully"})

class new_pydantic_model(BaseModel) :
    id : Annotated[Optional[str], Field(default=None, description="ID of the patient", example='P001')]
    name : Annotated[Optional[str], Field(default=None, description="Name of the patient", example="Prasad patil")]
    city : Annotated[Optional[str], Field(default=None, description="City of the patient", example="Pune")]
    age : Annotated[Optional[int], Field(default=None, description="Age of the patient", example=25)]
    gender : Annotated[Optional[Literal["Male", "Female", "Other"]], Field(default=None, description="Gender of the patient", example="Male")]
    height : Annotated[Optional[float], Field(default=None, description="Height of the patient in meters", example=1.75)]
    weight : Annotated[Optional[float], Field(default=None, description="Weight of the patient in kilograms", example=70.5)]
    
@app.put("/edit/{patient_id}") # using patient id as path parameter
def update_patient(patient_id: str, patient_detail: new_pydantic_model): # patient is class object containing data given by user to update
    data = ext_data()
    
    if patient_id not in data.keys() :
        raise HTTPException(status_code=404, detail="Patient not found to update details")
    
    required_patient = data[patient_id]
    
    dictionary = patient_detail.model_dump(exclude_unset=True) # unset = true means only the fields that are provided by user will be included in the dictionary, rest will be excluded
    
    for key, value in dictionary.items() : 
        required_patient[key] = value
        
    required_patient["id"] = patient_id # adding id to the dictionary to create new object of patient class   
    new_object_for_bmi_update = patient(**required_patient)
    
    data[patient_id] = new_object_for_bmi_update.model_dump(exclude = ['id']) # updating the data with new object of patient class
    save_data(data)
    
    return JSONResponse(status_code=200, content={"message": "Patient details updated successfully"})
    