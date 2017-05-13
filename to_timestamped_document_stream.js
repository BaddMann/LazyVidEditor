//https://blog.yld.io/2016/01/13/using-streams/#.WRZQJVXyuUk

var Transform = require('stream').Transform;  
var inherits = require('util').inherits;

module.exports = ToTimestampedDocTransform;

function ToTimestampedDocTransform(options) {  
  if ( ! (this instanceof JSONTransform))
    return new JSONTransform(options);

  if (! options) options = {};
  options.objectMode = true;
  Transform.call(this, options);
}

inherits(ToTimestampedDocTransform, Transform);

ToTimestampedDocTransform.prototype._transform = function _transform(temperature, encoding, callback) {  
  this.push({when: Date.now(), temperature: temperature});
  callback();
};