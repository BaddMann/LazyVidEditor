var net = require('net');
var TelnetInput = require('telnet-stream').TelnetInput;
var TelnetOutput = require('telnet-stream').TelnetOutput;
var dateTime = require('node-datetime');
var dt = dateTime.create();
var formatted = dt.format('Y-m-d_H-M');
var fs = require('fs');
var ws = fs.createWriteStream(formatted.concat('-Slides.txt'));
var websocket = require('websocket-stream');
var JSONStream = require('JSONStream');
var es = require('event-stream');

//Create TimeStamp Every Second and inject into File with newline
setInterval(function () {
    var dt = dateTime.create();
    var formatted = dt.format('Y-m-d H:M:S');
    ws.write(formatted.concat(' \r\n'));
    console.log(formatted);
 }, 1000);


var socket = net.createConnection(1702, '10.2.16.54', function() {
    var telnetInput = new TelnetInput();
    var telnetOutput = new TelnetOutput();
    var wss = websocket('ws://localhost:4444');
    
    wss.pipe(process.stdout);
    wss.pipe(ws);
    socket.pipe(telnetInput).pipe(process.stdout);
    process.stdin.pipe(telnetOutput).pipe(socket).pipe(ws);
});

function alive(){
    socket.write('sg\n')
}

function init(){
    socket.write('1WCV\n');
    socket.write('cgc 1\n');
    socket.write('cga 1 "Input 1 Mute"\n');
    socket.write('cga 1 "Input 2 Mute"\n');
    socket.write('cga 1 "Input 3 Mute"\n');
    socket.write('cga 1 "Input 4 Mute"\n');
    socket.write('cga 1 "Input 5 Mute"\n');
    socket.write('cga 1 "Input 6 Mute"\n');
    socket.write('cga 1 "Input 7 Mute"\n');
    socket.write('cga 1 "Input 8 Mute"\n');
    socket.write('cga 1 "Input 9 Mute"\n');
    socket.write('cga 1 "Input 10 Mute"\n');
    socket.write('cga 1 "Input 11 Mute"\n');
    socket.write('cga 1 "Input 12 Mute"\n');
    socket.write('cga 1 "Input 13 Mute"\n');
    socket.write('cga 1 "Input 14 Mute"\n');
    socket.write('cga 1 "Input 15 Mute"\n');
    socket.write('cgpna 1\n');
    socket.write('cgsna 1 500\n');
}


init();
setInterval(alive, 50000);



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
