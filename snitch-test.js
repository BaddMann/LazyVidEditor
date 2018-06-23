var fs           = require('fs'),
    StreamSnitch = require('stream-snitch'),
    albumList    = fs.createReadStream('./2018-06-08_17-43-Slides.txt'),
    cosmicSnitch = new StreamSnitch(/Evt0000?/m);


cosmicSnitch.on('match', console.log.bind(console));
albumList.pipe(cosmicSnitch);


function scrape(url, fn, cb) {
    http.get(url, function(res) {
      var snitch = new StreamSnitch(/<img.+src=["'](.+)['"].?>/gi);
      snitch.on('match', function(match) { fn(match[1]) });
      res.pipe(snitch);
      res.on('end', cb)
    });
  }

scrape("http://nuklearpower.com", console.log.bind(console))