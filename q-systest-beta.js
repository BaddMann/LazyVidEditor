var net = require('net');
var TelnetInput = require('telnet-stream').TelnetInput;
var TelnetOutput = require('telnet-stream').TelnetOutput;
var dateTime = require('node-datetime');
var fs = require('fs'); // Already here, but good to note for the require list
var path = require('path'); // Added for config path
var websocket = require('websocket-stream');
var JSONStream = require('JSONStream');
var StreamSnitch = require('stream-snitch');
var es = require('event-stream');
var cosmicSnitch = new StreamSnitch(/^Evt.*\s[\s\S]*?/gim);

// --- Configuration Loading ---
let config = {
    qsys_ip: "10.2.16.54",
    qsys_port: 1702,
    extron_ip: "10.2.16.50",
    extron_port: 23,
    obs_websocket_url: "ws://localhost:4444",
    log_file_prefix: "-Slides.txt",
    log_timestamp_interval_ms: 1000,
    keep_alive_interval_ms: 50000
};

// q-systest-beta.js is in the root, so config is in ./config/
const configPath = path.join(__dirname, 'config/node_logger_config.json'); 

try {
    if (fs.existsSync(configPath)) {
        const configFileContent = fs.readFileSync(configPath, 'utf-8');
        const loadedConfig = JSON.parse(configFileContent);
        config = { ...config, ...loadedConfig }; // Merge, allowing loaded to override defaults
        console.log('Loaded configuration from:', configPath);
    } else {
        console.log('Config file not found at:', configPath, '. Using default configuration.');
    }
} catch (error) {
    console.error('Error loading or parsing config file:', error, '. Using default configuration.');
}
// --- End Configuration Loading ---

var dt = dateTime.create();
var formatted = dt.format('Y-m-d_H-M');
var logfile = fs.createWriteStream(formatted.concat(config.log_file_prefix));


//Regex for timestamp plus first extron command (\d+-\d\d-\d\d\s\d\d:\d\d:\d\d)\s\n([A-Z]\w+),(\d,\d+,\d+)

//Regex the Complete Extron Output between two timecodes. maybe buggy, only works on completed logs, remove time stamps for telnetoutput: ^(\d+-\d\d-\d\d\s\d\d:\d\d:\d\d)\s\n(Evt.*\s[\s\S]*?)(\d+-\d\d-\d\d\s\d\d:\d\d:\d\d)\s

//Create TimeStamp Every Second and inject into File with newline
setInterval(function () {
    var dt = dateTime.create();
    var formatted = dt.format('Y-m-d H:M:S');
    logfile.write(formatted.concat(' \r\n'));
    console.log(formatted);
 }, config.log_timestamp_interval_ms);


var extronsocket = net.createConnection(config.extron_port, config.extron_ip, function() {
    var telnetInput = new TelnetInput();
    var telnetOutput = new TelnetOutput();
    extronsocket.pipe(telnetInput).pipe(cosmicSnitch);
    process.stdin.pipe(telnetOutput).pipe(extronsocket).pipe(logfile);
});

var qsyssocket = net.createConnection(config.qsys_port, config.qsys_ip, function() {
    var telnetInput = new TelnetInput();
    var telnetOutput = new TelnetOutput();
    var obssocket = websocket(config.obs_websocket_url);
    
    obssocket.pipe(process.stdout);
    obssocket.pipe(logfile);
    qsyssocket.pipe(telnetInput).pipe(cosmicSnitch);
    process.stdin.pipe(telnetOutput).pipe(qsyssocket).pipe(logfile);
});

function alive(){
    qsyssocket.write('sg\n')
    extronsocket.write('Q');
}

function init(){
    qsyssocket.write('cgc 1\n');
    qsyssocket.write('cga 1 "Input 1 Mute"\n');
    qsyssocket.write('cga 1 "Input 2 Mute"\n');
    qsyssocket.write('cga 1 "Input 3 Mute"\n');
    qsyssocket.write('cga 1 "Input 4 Mute"\n');
    qsyssocket.write('cga 1 "Input 5 Mute"\n');
    qsyssocket.write('cga 1 "Input 6 Mute"\n');
    qsyssocket.write('cga 1 "Input 7 Mute"\n');
    qsyssocket.write('cga 1 "Input 8 Mute"\n');
    qsyssocket.write('cga 1 "Input 9 Mute"\n');
    qsyssocket.write('cga 1 "Input 10 Mute"\n');
    qsyssocket.write('cga 1 "Input 11 Mute"\n');
    qsyssocket.write('cga 1 "Input 12 Mute"\n');
    qsyssocket.write('cga 1 "Input 13 Mute"\n');
    qsyssocket.write('cga 1 "Input 14 Mute"\n');
    qsyssocket.write('cga 1 "Input 15 Mute"\n');
    //qsyssocket.write('cga 1 "TruePeak/RMSMeterInput1Meter"\n');
    qsyssocket.write('cgpna 1\n');
    qsyssocket.write('cgsna 1 500\n'); // This 500ms is a Q-SYS specific command parameter, not from general config
    extronsocket.write('W1CV\r\n');
}


init();
setInterval(alive, config.keep_alive_interval_ms);

cosmicSnitch.on('match', console.log.bind(console));


//ToDo: Find way to poll telnet with SG command once a minute: Done
//      Format output from telnet stream into something more useful, JSON maybe
//      Create Variables based on Stream output and update state of variables based on continued stream
// ///Cool!     Integrate WebSocket Stream or call from it on another script... OBS WEB Socket stream is now being Consumed.
//      Learn how to emit and consume events better.
//      parse telnet output into JSON
//      emit timestamp only when data is added to pipe......
//      




// http://q-syshelp.qschome.com/Content/External%20Control/Q-SYS%20External%20Control/007%20Q-SYS%20External%20Control%20Protocol.htm
//http://webcache.googleusercontent.com/search?q=cache:Igc3wImsANsJ:q-syshelp.qschome.com/Content/External%2520Control/Q-SYS%2520External%2520Control/007%2520Q-SYS%2520External%2520Control%2520Protocol.htm+&cd=1&hl=en&ct=clnk&gl=us
