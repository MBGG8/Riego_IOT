let tempChart, humSueloChart, humAmbientalChart, luzChart;

// Variables para guardar datos históricos
const historyLength = 20;  // Cantidad de puntos a mostrar

const tempData = [];
const humSueloData = [];
const humAmbientalData = [];
const luzData = [];
const labels = [];

document.getElementById("riego-btn").addEventListener("click", function () {
  const card = document.getElementById("riego-card");
  const text = document.getElementById("riego-value");

  if (text.innerText === "Activo") {
    text.innerText = "Inactivo";
    card.classList.remove("bg-success");
    card.classList.add("bg-danger");
    this.innerText = "Activar Riego";
    this.classList.remove("btn-danger");
    this.classList.add("btn-success");
  } else {
    text.innerText = "Activo";
    card.classList.remove("bg-danger");
    card.classList.add("bg-success");
    this.innerText = "Desactivar Riego";
    this.classList.remove("btn-success");
    this.classList.add("btn-danger");
  }
});


function initCharts() {
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: { maxRotation: 45, minRotation: 45 },
      },
      y: {
        beginAtZero: true,
      }
    }
  };

  tempChart = new Chart(document.getElementById('tempChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Temperatura (°C)',
        data: tempData,
        borderColor: 'rgba(220,53,69,1)',
        backgroundColor: 'rgba(220,53,69,0.2)',
        fill: true,
        tension: 0.3,
      }]
    },
    options: commonOptions
  });

  humSueloChart = new Chart(document.getElementById('humSueloChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Humedad del Suelo (%)',
        data: humSueloData,
        borderColor: 'rgba(40,167,69,1)',
        backgroundColor: 'rgba(40,167,69,0.2)',
        fill: true,
        tension: 0.3,
      }]
    },
    options: commonOptions
  });

  humAmbientalChart = new Chart(document.getElementById('humAmbientalChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Humedad Ambiental (%)',
        data: humAmbientalData,
        borderColor: 'rgba(23,162,184,1)',
        backgroundColor: 'rgba(23,162,184,0.2)',
        fill: true,
        tension: 0.3,
      }]
    },
    options: commonOptions
  });

  luzChart = new Chart(document.getElementById('luzChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Luminosidad (lx)',
        data: luzData,
        borderColor: 'rgba(255,193,7,1)',
        backgroundColor: 'rgba(255,193,7,0.2)',
        fill: true,
        tension: 0.3,
      }]
    },
    options: commonOptions
  });
}

function actualizarDatos() {
  $.get("/data", function(data) {
    $("#error-message").addClass("d-none");

    // Actualiza cards
    $("#temp-value").text(data.temperatura !== undefined ? data.temperatura + "°C" : "--");
    $("#hum-suelo-value").text(data.humedad_suelo !== undefined ? data.humedad_suelo + "%" : "--");
    $("#hum-ambiental-value").text(data.humedad_ambiental !== undefined ? data.humedad_ambiental + "%" : "--");
    $("#luz-value").text(data.luminosidad !== undefined ? data.luminosidad + " lx" : "--");

    // Actualiza riego
    if (data.activaciones !== undefined) {
      const activo = data.activaciones;
      $("#riego-value").text(activo ? "Activo" : "Inactivo");
      $("#riego-card").removeClass("bg-success bg-danger")
                      .addClass(activo ? "bg-success" : "bg-danger");

      $("#riego-btn").removeClass("btn-success btn-danger")
                     .addClass(activo ? "btn-danger" : "btn-success")
                     .text(activo ? "Desactivar Riego" : "Activar Riego");
    } else {
      $("#riego-value").text("--");
      $("#riego-card").removeClass("bg-success bg-danger").addClass("bg-danger");
      $("#riego-btn").removeClass("btn-success btn-danger").addClass("btn-success").text("Activar Riego");
    }

    // Actualiza históricos para gráficos
    const now = new Date().toLocaleTimeString();

    if (labels.length >= historyLength) {
      labels.shift();
      tempData.shift();
      humSueloData.shift();
      humAmbientalData.shift();
      luzData.shift();
    }
    labels.push(now);
    tempData.push(data.temperatura !== undefined ? data.temperatura : null);
    humSueloData.push(data.humedad_suelo !== undefined ? data.humedad_suelo : null);
    humAmbientalData.push(data.humedad_ambiental !== undefined ? data.humedad_ambiental : null);
    luzData.push(data.luminosidad !== undefined ? data.luminosidad : null);

    tempChart.update();
    humSueloChart.update();
    humAmbientalChart.update();
    luzChart.update();

  }).fail(function() {
    $("#error-message").removeClass("d-none");

    // Valores por defecto en error
    $("#temp-value, #hum-suelo-value, #hum-ambiental-value, #luz-value, #riego-value")
      .text("--");

    $("#riego-card").removeClass("bg-success").addClass("bg-danger");
    $("#riego-btn").removeClass("btn-danger").addClass("btn-success").text("Activar Riego");
  });
}

$("#riego-btn").click(function() {
  const activar = $(this).text().includes("Activar");
  $.ajax({
    url: "/riego",
    type: "POST",
    data: JSON.stringify({ activar }),
    contentType: "application/json",
    success: function() {
      alert("Comando enviado al ESP32");
      // El cambio visual real se actualizará en la siguiente consulta a /data
    },
    error: function() {
      alert("Error al enviar comando");
    }
  });
});

$(document).ready(function() {
  initCharts();
  actualizarDatos();
  setInterval(actualizarDatos, 5000);
});
