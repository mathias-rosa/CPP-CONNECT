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