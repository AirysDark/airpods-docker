const socket = io();
const ctx = document.getElementById("headGraph").getContext("2d");

let headX = [], headY = [], headZ = [];

// =========================
// API Calls
// =========================
function connect() { fetch('/connect'); }
function setNoise(m) { fetch('/noise/' + m); }
function setCA(v) { fetch('/ca/' + v); }
function setAdaptive(l) { fetch('/adaptive/' + l); }
function recStart() { fetch('/record/start'); }
function recStop() { fetch('/record/stop'); }
function recReplay() { fetch('/record/replay'); }

function sendRaw() {
  const hex = document.getElementById("rawInput").value.trim();
  if (!hex.match(/^[0-9a-fA-F ]+$/)) { alert("Invalid HEX"); return; }
  fetch('/raw', { method: 'POST', body: hex });
}

// Slider live update
document.getElementById("adaptiveSlider").addEventListener("input", e => setAdaptive(e.target.value));

// =========================
// Helpers
// =========================
function getBatteryClass(val) {
  if (val < 20) return "low";
  if (val < 60) return "mid";
  return "high";
}

// =========================
// Scan & Pair Functions
// =========================
async function scanDevices() {
  const res = await fetch("/scan");
  const data = await res.json();
  const select = document.getElementById("deviceList");
  select.innerHTML = "";
  if (data.devices && data.devices.length) {
    data.devices.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d.mac;
      opt.text = `${d.name} (${d.mac})`;
      select.add(opt);
    });
  } else {
    alert("No AirPods found");
  }
}

async function pairDevice() {
  const mac = document.getElementById("deviceList").value;
  if (!mac) { alert("Select a device"); return; }
  const res = await fetch("/pair/" + mac);
  const data = await res.json();
  if (data.status === "paired") {
    alert("Paired & connected: " + mac);
  } else {
    alert("Error: " + JSON.stringify(data));
  }
}

// =========================
// WebSocket Live Updates
// =========================
socket.on("state", (data) => {

  // Connection status
  document.getElementById("connStatus").className = "status connected";
  document.getElementById("connStatus").innerText = "Connected";

  // Raw JSON
  document.getElementById("status").innerText = JSON.stringify(data, null, 2);

  // Battery
  let html = "";
  if (data.battery) {
    for (let k in data.battery) {
      let lvl = data.battery[k].level;
      let cls = getBatteryClass(lvl);
      html += `<div>${k}</div><div class="bar"><div class="fill ${cls}" style="width:${lvl}%">${lvl}%</div></div>`;
    }
  }
  document.getElementById("battery").innerHTML = html;

  // Mode indicator
  const modes = ["Off","ANC","Transparency","Adaptive"];
  let mhtml = "";
  modes.forEach(m => {
    const active = (m === data.noise_mode) ? "active" : "";
    mhtml += `<span class="mode ${active}">${m}</span>`;
  });
  document.getElementById("modeStatus").innerHTML = mhtml;

  // Head tracking
  if (data.head && data.head.orientation) {
    const [x,y,z] = data.head.orientation;
    headX.push(x); headY.push(y); headZ.push(z);
    if (headX.length > 60) { headX.shift(); headY.shift(); headZ.shift(); }
    ctx.clearRect(0, 0, 400, 150);
    function drawLine(arr, color, offset) {
      ctx.beginPath();
      arr.forEach((v,i) => ctx.lineTo(i*6, offset + (v/50)));
      ctx.strokeStyle = color; ctx.stroke();
    }
    drawLine(headX,"#ff4444",40);
    drawLine(headY,"#00ff88",80);
    drawLine(headZ,"#00aaff",120);
  }

});

// Handle disconnect
socket.on("disconnect", () => {
  document.getElementById("connStatus").className = "status disconnected";
  document.getElementById("connStatus").innerText = "Disconnected";
});