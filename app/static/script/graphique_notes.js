console.log(notes);

notes.forEach(element => {

    obj = {}

    element.slice(2).forEach(note => {
        obj[note.nom_note] = note.note;
    });

    console.log(obj);

    let graph = document.createElement("canvas");
    let newGraph = new Chart(graph, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: element[0],
                    data: obj,
                    backgroundColor:"blue",
                    hoverBorderWidth: 10,
                    hoverBorderRadius: 30,
                    BorderRadius: 30,
                }
            ]
        }
    })
    let graphe_moyennes = document.querySelector(".graphe_moyennes");
    let div = document.createElement("div");
    div.className = "div-graph";
    div.appendChild(graph);
    graphe_moyennes.appendChild(div);

});

const graph = document.getElementById("graph").getContext('2d')
console.log(moyennes)
let myChart = new Chart(graph, {
    type: "bar",
    data: {
        datasets: [
            {
                label: "ta mère en slip",
                data: moyennes,
                backgroundColor:"blue",
                hoverBorderWidth: 10,
                hoverBorderRadius: 30,
                BorderRadius: 30,
            }
        ]
    }
})