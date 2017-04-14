document.getElementById('fileInput').onchange = function () {
    var filename;
    filename = this.value.split('\\');
    filename = filename[filename.length - 1];
    document.getElementById("filename-dis").value = filename;
};
