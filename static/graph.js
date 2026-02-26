function drawGraph(graphData) {
    const container = document.getElementById('career-graph');
    container.innerHTML = ''; // Clear previous graph

    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
        // Fallback demo graph if Neo4j is not connected yet
        graphData = {
            nodes: [
                { id: "Current You", group: 1, type: "user" },
                { id: "Python", group: 2, type: "skill_owned" },
                { id: "Data Analysis", group: 2, type: "skill_owned" },
                { id: "Machine Learning", group: 4, type: "skill_missing" },
                { id: "Docker", group: 4, type: "skill_missing" },
                { id: "Data Scientist", group: 3, type: "job" }
            ],
            links: [
                { source: "Current You", target: "Python", value: 1, label: "HAS_SKILL" },
                { source: "Current You", target: "Data Analysis", value: 1, label: "HAS_SKILL" },
                { source: "Data Scientist", target: "Python", value: 1, label: "REQUIRES" },
                { source: "Data Scientist", target: "Data Analysis", value: 1, label: "REQUIRES" },
                { source: "Data Scientist", target: "Machine Learning", value: 1, label: "REQUIRES" },
                { source: "Data Scientist", target: "Docker", value: 1, label: "REQUIRES" }
            ]
        };
        const msg = document.createElement('p');
        msg.className = "text-sm text-gray-500 text-center m-2";
        msg.innerText = "(Showing Demo Graph: Neo4j backend not connected)";
        container.appendChild(msg);
    }

    const width = container.clientWidth;
    const height = container.clientHeight - 40; // Adjust for text

    const color = d3.scaleOrdinal()
        .domain([1, 2, 3, 4])
        .range(["#3498db", "#2ecc71", "#9b59b6", "#e74c3c"]);
    // 1: User (Blue), 2: Owned Skill (Green), 3: Job (Purple), 4: Missing Skill (Red)

    const simulation = d3.forceSimulation(graphData.nodes)
        .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2));

    const svg = d3.select("#career-graph").append("svg")
        .attr("width", width)
        .attr("height", height);

    // Add arrowheads for directed edges
    svg.append("defs").selectAll("marker")
        .data(["end"])
        .enter().append("marker")
        .attr("id", "arrow")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 25)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("fill", "#999")
        .attr("d", "M0,-5L10,0L0,5");

    const link = svg.append("g")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .selectAll("line")
        .data(graphData.links)
        .join("line")
        .attr("stroke-width", 2)
        .attr("marker-end", "url(#arrow)");

    const linkLabels = svg.append("g")
        .selectAll("text")
        .data(graphData.links)
        .join("text")
        .attr("font-size", "10px")
        .attr("fill", "#666")
        .text(d => d.label);

    const node = svg.append("g")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
        .selectAll("circle")
        .data(graphData.nodes)
        .join("circle")
        .attr("r", 15)
        .attr("fill", d => color(d.group))
        .call(drag(simulation));

    node.append("title")
        .text(d => d.id);

    const labels = svg.append("g")
        .selectAll("text")
        .data(graphData.nodes)
        .join("text")
        .attr("dx", 18)
        .attr("dy", ".35em")
        .text(d => d.id)
        .attr("font-size", "12px")
        .attr("fill", "#333");

    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        labels
            .attr("x", d => d.x)
            .attr("y", d => d.y);

        linkLabels
            .attr("x", d => (d.source.x + d.target.x) / 2)
            .attr("y", d => (d.source.y + d.target.y) / 2);
    });

    function drag(simulation) {
        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }
        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }
        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }
        return d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);
    }
}

// Attach to the global window object so app.js can call it
window.fetchAndDrawGraph = function (targetJob = null) {
    let url = '/api/graph-data?user_id=current_user';
    if (targetJob) {
        url += '&target_job=' + encodeURIComponent(targetJob);
    }

    fetch(url)
        .then(res => res.json())
        .then(data => {
            drawGraph(data);
        })
        .catch(err => {
            console.error("Error fetching graph data:", err);
            drawGraph(null); // Will draw the demo fallback
        });
};
