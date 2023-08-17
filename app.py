import uvicorn
from fastapi import FastAPI
from AdvertisingModel import optimize_budget_func, OptimizationInput

app = FastAPI()

@app.post('/')
def show_outcome(input_data: OptimizationInput):
    val1, val2 = optimize_budget_func(input_data)
    return val1, val2

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
    
# uvicorn app:app --reload
# http://127.0.0.1:8000/docs