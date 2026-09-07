const API="https://krishicare-farmer.onrender.com/api";
let weather={temperature:31,rain_probability:20};

async function loadWeather(){
  try{
    const r=await fetch(API+"/weather?latitude=28.61&longitude=77.23");
    weather=await r.json();
    document.getElementById("temp").textContent=(weather.temperature??"--")+"°C";
    document.getElementById("rain").textContent=(weather.rain_probability??"--")+"%";
  }catch(e){document.getElementById("temp").textContent="Offline";document.getElementById("rain").textContent="--";}
}
function getMoisture(){return Number(document.getElementById("soil").value||28)}
async function getAI(){
  const moisture=getMoisture();
  document.getElementById("moisture").textContent=moisture+"%";
  const url=`${API}/ai/recommendation?soil_moisture=${moisture}&temperature=${weather.temperature||31}&rain_probability=${weather.rain_probability||20}`;
  try{const d=await (await fetch(url,{method:"POST"})).json();document.getElementById("ai").textContent=d.action+" "+d.prediction;}
  catch(e){document.getElementById("ai").textContent="Backend is not running yet. Start FastAPI using the README instructions."}
}
async function saveFarmer(){
  const data={name:name.value,phone:phone.value,location:location.value,crop:cropInput.value};
  try{const d=await (await fetch(API+"/farmers",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)})).json();
  farmerId.value=d.id; saveMsg.textContent="Saved! Farmer ID: "+d.id;}catch(e){saveMsg.textContent="Start the backend first."}
}
async function saveObservation(){
  const data={farmer_id:Number(farmerId.value),soil_moisture:Number(soil.value),temperature:Number(fieldTemp.value),note:note.value};
  try{const d=await (await fetch(API+"/observations",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)})).json();
  obsMsg.textContent=d.message||"Saved";}catch(e){obsMsg.textContent="Check Farmer ID and backend."}
}
function loadAll(){loadWeather();getAI()}
loadWeather();getAI();
