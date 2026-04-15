function submitLeave(){

    const name = document.getElementById("name").value;
    const type = document.getElementById("type").value;
    const start = document.getElementById("start").value;
    const end = document.getElementById("end").value;
    const reason = document.getElementById("reason").value;

    const result = document.getElementById("result");

    if(!name || !type || !start || !end || !reason){
        result.innerHTML = "<div class='warning'>Please fill all fields properly.</div>";
        return;
    }

    let tasks = Math.floor(Math.random()*5);
    let deadlines = Math.floor(Math.random()*3);

    document.getElementById("tasks").innerText = tasks;
    document.getElementById("deadlines").innerText = deadlines;

    if(tasks > 3 || deadlines > 1){
        result.innerHTML = `
        <div class="warning">
            High Workload Detected ⚠️ <br>
            Manager Approval Required
        </div>`;
    }
    else{
        result.innerHTML = `
        <div class="success">
            Leave Auto-Approved Successfully 
        </div>`;
    }
}