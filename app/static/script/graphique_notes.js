let style = getComputedStyle(document.body);

notes.forEach((matiere) => {
  if (matiere.length > 2 + 1) {
    let obj = {};

    matiere.slice(2).forEach((note) => {
      obj[note.nom_note] = note.note;
    });

    let graph = document.createElement("canvas");
    let newGraph = new Chart(graph, {
      type: "line",
      options: {
        elements: {
          point: {
            pointStyle: "rectRounded",
            borderColor:
              "hsl(" + style.getPropertyValue("--accent-color") + ")",
            radius: 5,
          },
        },
        scales: {
          y: {
            suggestedMin: 0,
            suggestedMax: 20,
          },
        },
        plugins: {
            autocolors: false,
            annotation: {
              annotations: {
                line1: {
                  type: 'line',
                  yMin: matiere[1],
                  yMax: matiere[1],
                  borderColor: "hsl(" + style.getPropertyValue("--accent-color") + ")",
                  borderWidth: 2,
                  borderDash: [15, 15],
                },
                label1: {
                    type: 'label',
                    xValue:  0,
                    yValue:  matiere[1] + 1.8,
                    color: "hsl(" + style.getPropertyValue("--accent-color") + ")",
                    content: ['Moyenne'],
                    font: {
                      size: 12,
                      family: 'Poppins',
                    },
                    position : 'start'
                  },
              }
            }
          }
      },
      data: {
        datasets: [
          {
            label: matiere[0],
            data: obj,
            backgroundColor:
              "hsl(" + style.getPropertyValue("--accent-color") + ")",
            hoverBorderWidth: 10,
            hoverBorderRadius: 30,
            BorderRadius: 30,
          },
        ],
      },
      
    });
    let graphe_moyennes = document.querySelector(".graphe_moyennes");
    let div = document.createElement("div");
    div.className = "div-graph";
    div.appendChild(graph);
    graphe_moyennes.appendChild(div);
  }
});

const graph = document.getElementById("graph").getContext("2d");
let myChart = new Chart(graph, {
  type: "bar",
  options: {
    radius: 3,
  },
  data: {
    datasets: [
      {
        label: "Moyennes des matières",
        data: moyennes,
        backgroundColor:
          "hsl(" + style.getPropertyValue("--accent-color") + ")",
        hoverBorderWidth: 10,
        hoverBorderRadius: 20,
        borderRadius: 10,
      },
    ],
  },
});
