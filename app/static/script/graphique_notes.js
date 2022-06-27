let style = getComputedStyle(document.body);

let semestre = JSON.parse(window.localStorage.getItem("semestre"));

let graphe_moyennes = document.getElementsByClassName("graphe_moyennes");


window.afficheNotes = async function afficheNotes(semestre) {

  while (graphe_moyennes.firstChild) {
    graphe_moyennes.removeChild(graphe_moyennes.lastChild);
  }


  let matières = await getNotes();
  matières = matières["semestre" + semestre]
    
  let moyenne_generale = {}

  let graph = document.createElement("canvas");
  let myChart = new Chart(graph, {
    type: "bar",
    options: {
      radius: 3,
      plugins: {
        autocolors: false,
        annotation: {
          annotations: {
            line1: {
              type: 'line',
              yMin: matières.moyenne,
              yMax: matières.moyenne,
              borderColor: "hsl(" + style.getPropertyValue("--accent-color") + ")",
              borderWidth: 2,
              borderDash: [15, 15],
            },
            label1: {
                type: 'label',
                xValue:  0,
                yValue:  matières.moyenne + 1.8,
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
      },
    },
    data: {
      datasets: [
        {
          label: "Moyennes des matières",
          data: moyenne_generale,
          backgroundColor:
            "hsl(" + style.getPropertyValue("--accent-color") + ")",
          hoverBorderWidth: 10,
          hoverBorderRadius: 20,
          borderRadius: 10,
        },
      ],
    },
  });
  
  graphe_moyennes = document.querySelector(".graphe_moyennes");
  let div = document.createElement("div");
  div.className = "div-graph";
  div.style.marginTop = "0";
  div.appendChild(graph);
  graphe_moyennes.appendChild(div);

  matières.notes.forEach((matiere) => {

    moyenne_generale[matiere.name] = matiere.moyenne;

      if (matiere.notes.length > 2) {
        let obj = {};

        matiere.notes.forEach((note) => {
          obj[note.name] = note.note;
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
                      yMin: matiere.moyenne,
                      yMax: matiere.moyenne,
                      borderColor: "hsl(" + style.getPropertyValue("--accent-color") + ")",
                      borderWidth: 2,
                      borderDash: [15, 15],
                    },
                    label1: {
                        type: 'label',
                        xValue:  0,
                        yValue:  matiere.moyenne + 1.8,
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
                label: matiere.name,
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
}
