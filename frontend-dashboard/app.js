const API_BASE =
"https://069z9dwdg7.execute-api.ap-south-1.amazonaws.com/prod";

let stabilityChart;
let breakdownChart;


async function loadScores(){

const response = await fetch(`${API_BASE}/scores`);
const scores = await response.json();

populateDropdown(scores);
renderStabilityChart(scores);

}


function populateDropdown(scores){

const select = document.getElementById("conditionSelect");

select.innerHTML="";

scores.forEach(s => {

const option = document.createElement("option");

option.value = s.condition_treatment;
option.text = s.condition_treatment;

select.appendChild(option);

});

select.addEventListener("change", loadPapers);

loadPapers();

}


function renderStabilityChart(scores){

const labels = scores.map(s => s.condition_treatment);

const values = scores.map(s => s.stability_score);

const ctx = document.getElementById("stabilityChart").getContext("2d");

if(stabilityChart) stabilityChart.destroy();

stabilityChart = new Chart(ctx,{

type:"bar",

data:{
labels:labels,
datasets:[{
label:"Stability Score",
data:values,
backgroundColor:"#4CAF50"
}]
},

options:{
responsive:true,
maintainAspectRatio:false,
scales:{
y:{
beginAtZero:true,
max:100
}
}
}

});

}


async function loadPapers(){

const select = document.getElementById("conditionSelect");

const value = select.value;

if(!value) return;

const parts = value.split("#");

const condition = parts[0];
const treatment = parts[1];

const url =
`${API_BASE}/findings?condition=${condition}&treatment=${treatment}`;

const response = await fetch(url);

const papers = await response.json();

displayPapers(papers);
renderBreakdownChart(papers);

fetch(`${API_BASE}/scores`)
.then(res => res.json())
.then(scores => {

const key = `${condition}#${treatment}`;

const item = scores.find(s => s.condition_treatment === key);

if(item){

renderConsensusGauge(item.stability_score);

}

});

}


function displayPapers(papers){

const container = document.getElementById("papers");

container.innerHTML="";

if(papers.length===0){

container.innerHTML="No papers found";

return;

}

papers.forEach(p => {

const div = document.createElement("div");

div.className="paper";

div.innerHTML = `
<b>PubMed ${p.pubmed_id}</b><br><br>

${p.conclusion_summary}<br><br>

<b>Direction:</b> ${p.direction_of_effect}<br>
<b>Confidence:</b> ${p.confidence_level}<br>
<b>Evidence Strength:</b> ${p.evidence_strength_score}<br>

<a target="_blank"
href="https://pubmed.ncbi.nlm.nih.gov/${p.pubmed_id}">
View Paper
</a>
`;

container.appendChild(div);

});

}

function renderConsensusGauge(score){

const gauge = document.getElementById("consensusGauge");
const label = document.getElementById("consensusLabel");

let current = 0;

const interval = setInterval(()=>{

current++;

gauge.innerText = current + "%";

if(current >= score){

clearInterval(interval);

}

},15);

if(score >= 80){

gauge.style.color = "#2ecc71";
label.innerText = "Strong Scientific Consensus";

}

else if(score >= 50){

gauge.style.color = "#f39c12";
label.innerText = "Moderate Evidence";

}

else{

gauge.style.color = "#e74c3c";
label.innerText = "Conflicting or Weak Evidence";

}

}


function renderBreakdownChart(papers){

let supports=0;
let contradicts=0;
let neutral=0;

papers.forEach(p => {

if(p.direction_of_effect==="supports") supports++;

else if(p.direction_of_effect==="contradicts") contradicts++;

else neutral++;

});

const ctx = document.getElementById("breakdownChart").getContext("2d");

if(breakdownChart) breakdownChart.destroy();

breakdownChart = new Chart(ctx,{

type:"pie",

data:{
labels:["Supports","Contradicts","Neutral"],

datasets:[{
data:[supports,contradicts,neutral],
backgroundColor:["#4CAF50","#FF5252","#FFC107"]
}]
},

options:{
responsive:true,
maintainAspectRatio:false
}

});

}


async function searchResearch(){

const condition =
document.getElementById("conditionInput").value.trim();

const treatment =
document.getElementById("treatmentInput").value.trim();

if(!condition || !treatment){
alert("Please enter condition and treatment");
return;
}

const url =
`${API_BASE}/findings?condition=${condition}&treatment=${treatment}`;

const response = await fetch(url);
const data = await response.json();

if(data.message){
alert(data.message);
return;
}

/* show papers */
displayPapers(data);

/* update chart */
renderBreakdownChart(data);

/* add searched item to dropdown */

const select = document.getElementById("conditionSelect");

const key = `${condition}#${treatment}`;

let exists = false;

for(let i=0;i<select.options.length;i++){
if(select.options[i].value === key){
exists = true;
break;
}
}

if(!exists){

const option = document.createElement("option");

option.value = key;
option.text = key;

select.appendChild(option);

}

select.value = key;

}


loadScores();