"use strict";

var crypto = require('crypto');
var assert = require('assert');
var util = require('util');
var BigInteger = require('./jsbn');

var zero = new BigInteger(0);

function assert_(val, msg) {
  if (!val)
    throw new Error(msg||"assertion");
}

/*
 * If a conversion is explicitly specified with the operator PAD(),
 * the integer will first be implicitly converted, then the resultant
 * byte-string will be left-padded with zeros (if necessary) until its
 * length equals the implicitly-converted length of N.
 *
 * params:
 *         n (buffer)       Number to pad
 *         len (int)        length of the resulting Buffer
 *
 * returns: buffer
 */
function padTo(n, len) {
  assertIsBuffer(n, "n");
  var padding = len - n.length;
  assert_(padding > -1, "Negative padding.  Very uncomfortable.");
  var result = new Buffer(len);
  result.fill(0, 0, padding);
  n.copy(result, padding);
  assert.equal(result.length, len);
  return result;
};

function padToN(number, params) {
  assertIsBigInteger(number);
  var n = number.toString(16).length % 2 != 0 ? "0" + number.toString(16) : number.toString(16);
  return padTo(new Buffer(n, 'hex'), params.N_length_bits / 8);
}

function assertIsBuffer(arg, argname) {
  argname = argname || "arg";
  assert_(Buffer.isBuffer(arg), "Type error: "+argname+" must be a buffer");
}

function assertIsBigInteger(arg) {
  assert_(arg.constructor.name === 'BigInteger', "Type error: " + arg.argname + " must be a BigInteger");
}

/*
 * compute the intermediate value x as a hash of three buffers:
 * salt, identity, and password.  And a colon.  FOUR buffers.
 *
 *      x = H(s | H(I | ":" | P))
 *
 * params:
 *         salt (buffer)    salt
 *         I (buffer)       user identity
 *         P (buffer)       user password
 *
 * returns: x (bignum)      user secret
 */
function getx(params, salt, I, P) {
  assertIsBuffer(salt, "salt (salt)");
  assertIsBuffer(I, "identity (I)");
  assertIsBuffer(P, "password (P)");
  var hashIP = crypto.createHash(params.hash)
    .update(Buffer.concat([I, new Buffer(':'), P]))
    .digest();
  var hashX = crypto.createHash(params.hash)
    .update(salt)
    .update(hashIP)
    .digest();
  return(new BigInteger(hashX));
};

/*
 * The verifier is calculated as described in Section 3 of [SRP-RFC].
 * We give the algorithm here for convenience.
 *
 * The verifier (v) is computed based on the salt (s), user name (I),
 * password (P), and group parameters (N, g).
 *
 *         x = H(s | H(I | ":" | P))
 *         v = g^x % N
 *
 * params:
 *         params (obj)     group parameters, with .N, .g, .hash
 *         salt (buffer)    salt
 *         I (buffer)       user identity
 *         P (buffer)       user password
 *
 * returns: buffer
 */
function computeVerifier(params, salt, I, P) {
  assertIsBuffer(salt, "salt (salt)");
  assertIsBuffer(I, "identity (I)");
  assertIsBuffer(P, "password (P)");
  var v_num = params.g.modPow(getx(params, salt, I, P), params.N);
  return v_num.toBuffer(true);
};

/*
 * calculate the SRP-6 multiplier
 *
 * params:
 *         params (obj)     group parameters, with .N, .g, .hash
 *
 * returns: bignum
 */
function getk(params) {
  var k_buf = crypto
    .createHash(params.hash)
    .update(padToN(params.N, params))
    .update(padToN(params.g, params))
    .digest();
  return(new BigInteger(k_buf));
};

/*
 * Generate a random key
 *
 * params:
 *         bytes (int)      length of key (default=32)
 *         callback (func)  function to call with err,key
 *
 * returns: nothing, but runs callback with a Buffer
 */
function genKey(bytes, callback) {
  // bytes is optional
  if (arguments.length < 2) {
    callback = bytes;
    bytes = 32;
  }
  if (typeof callback !== 'function') {
    throw("Callback required");
  }
  crypto.randomBytes(bytes, function(err, buf) {
    if (err) return callback (err);
    return callback(null, buf);
  });
};

/*
 * The server key exchange message also contains the server's public
 * value (B).  The server calculates this value as B = k*v + g^b % N,
 * where b is a random number that SHOULD be at least 256 bits in length
 * and k = H(N | PAD(g)).
 *
 * Note: as the tests imply, the entire expression is mod N.
 *
 * params:
 *         params (obj)     group parameters, with .N, .g, .hash
 *         v (bignum)       verifier (stored)
 *         b (bignum)       server secret exponent
 *
 * returns: B (buffer)      the server public message
 */
function getB(params, k, v, b) {
  assertIsBigInteger(v);
  assertIsBigInteger(k);
  assertIsBigInteger(b);
  var N = params.N;
  var r = k.multiply(v).add(params.g.modPow(b, N)).mod(N);
  return r.toBuffer(true);
};

/*
 * The client key exchange message carries the client's public value
 * (A).  The client calculates this value as A = g^a % N, where a is a
 * random number that SHOULD be at least 256 bits in length.
 *
 * Note: for this implementation, we take that to mean 256/8 bytes.
 *
 * params:
 *         params (obj)     group parameters, with .N, .g, .hash
 *         a (bignum)       client secret exponent
 *
 * returns A (bignum)       the client public message
 */
function getA(params, a_num) {
  assertIsBigInteger(a_num);
  if (Math.ceil(a_num.toString(16).length / 2) < 32) {
    console.warn("getA: client key length", a_num.bitLength(), "is less than the recommended 256 bits");
  }
  return params.g.modPow(a_num, params.N).toBuffer(true);
};

/*
 * getu() hashes the two public messages together, to obtain a scrambling
 * parameter "u" which cannot be predicted by either party ahead of time.
 * This makes it safe to use the message ordering defined in the SRP-6a
 * paper, in which the server reveals their "B" value before the client
 * commits to their "A" value.
 *
 * params:
 *         params (obj)     group parameters, with .N, .g, .hash
 *         A (Buffer)       client ephemeral public key
 *         B (Buffer)       server ephemeral public key
 *
 * returns: u (bignum)      shared scrambling parameter
 */
function getu(params, A, B) {
  assertIsBuffer(A, params, "A");
  assertIsBuffer(B, params, "B");
  var u_buf = crypto.createHash(params.hash)
    .update(padTo(A, params.N_length_bits / 8))
    .update(padTo(B, params.N_length_bits / 8))
    .digest();
  return(new BigInteger(u_buf));
};

/*
 * The TLS premaster secret as calculated by the client
 *
 * params:
 *         params (obj)     group parameters, with .N, .g, .hash
 *         salt (buffer)    salt (read from server)
 *         I (buffer)       user identity (read from user)
 *         P (buffer)       user password (read from user)
 *         a (bignum)       ephemeral private key (generated for session)
 *         B (bignum)       server ephemeral public key (read from server)
 *
 * returns: buffer
 */

function client_getS(params, k_num, x_num, a_num, B_num, u_num) {
  assertIsBigInteger(k_num);
  assertIsBigInteger(x_num);
  assertIsBigInteger(a_num);
  assertIsBigInteger(B_num);
  assertIsBigInteger(u_num);
  if((zero.compareTo(B_num) > 0) && (N.compareTo(B_num) < 0))
    throw new Error("invalid server-supplied 'B', must be 1..N-1");
  var S_num = B_num.subtract(k_num.multiply(params.g.modPow(x_num, params.N))).modPow(a_num.add(u_num.multiply(x_num)), params.N).mod(params.N);
  return S_num.toBuffer(true);
};

/*
 * The TLS premastersecret as calculated by the server
 *
 * params:
 *         params (obj)     group parameters, with .N, .g, .hash
 *         v (bignum)       verifier (stored on server)
 *         A (bignum)       ephemeral client public key (read from client)
 *         b (bignum)       server ephemeral private key (generated for session)
 *
 * returns: bignum
 */

function server_getS(params, v_num, A_num, b_num, u_num) {
  assertIsBigInteger(v_num);
  assertIsBigInteger(A_num);
  assertIsBigInteger(b_num);
  assertIsBigInteger(u_num);
  if((zero.compareTo(A_num) > 0) && (N.compareTo(A_num) < 0))
    throw new Error("invalid client-supplied 'A', must be 1..N-1");
  var S_num = A_num.multiply(v_num.modPow(u_num, params.N)).modPow(b_num, params.N).mod(params.N);
  return S_num.toBuffer(true);
};

/*
 * Compute the shared session key K from S
 *
 * params:
 *         params (obj)     group parameters, with .N, .g, .hash
 *         S (buffer)       Session key
 *
 * returns: buffer
 */
function getK(params, S_buf) {
  assertIsBuffer(S_buf, params, "S");
  if (params.hash === "sha1") {
    // use t_mgf1 interleave for short sha1 hashes
    return Buffer.concat([
      crypto.createHash(params.hash).update(S_buf).update(Buffer.from([0,0,0,0])).digest(),
      crypto.createHash(params.hash).update(S_buf).update(Buffer.from([0,0,0,1])).digest()
    ]);
  } else {
    // use hash as-is otherwise
    return crypto.createHash(params.hash).update(S_buf).digest();
  }
};

function getM1(params, u_buf, s_buf, A_buf, B_buf, K_buf) {
  assertIsBuffer(u_buf, params, "identity (I)");
  assertIsBuffer(s_buf, params, "salt (s)")
  assertIsBuffer(A_buf, params, "A");
  assertIsBuffer(B_buf, params, "B");
  assertIsBuffer(K_buf, params, "K");

  var hN = crypto.createHash(params.hash).update(params.N.toBuffer(true)).digest();
  var hG = crypto.createHash(params.hash).update(params.g.toBuffer(true)).digest();

  for (var i = 0; i < hN.length; i++)
    hN[i] ^= hG[i];

  var hU = crypto.createHash(params.hash).update(u_buf).digest();

  return crypto.createHash(params.hash)
    .update(hN).update(hU).update(s_buf)
    .update(A_buf).update(B_buf).update(K_buf)
    .digest();
}

function getM2(params, A_buf, M1_buf, K_buf) {
  assertIsBuffer(A_buf, params, "A");
  assertIsBuffer(M1_buf, params, "M1");
  assertIsBuffer(K_buf, params, "K");

  return crypto.createHash(params.hash)
    .update(A_buf).update(M1_buf).update(K_buf)
    .digest();
}

function equal(buf1, buf2) {
  // constant-time comparison. A drop in the ocean compared to our
  // non-constant-time modexp operations, but still good practice.
  return buf1.toString('hex') === buf2.toString('hex');
}

function Client(params, salt_buf, identity_buf, password_buf, secret1_buf) {
  if (!(this instanceof Client)) {
    return new Client(params, salt_buf, identity_buf, password_buf, secret1_buf);
  }
  assertIsBuffer(salt_buf, "salt (s)");
  assertIsBuffer(identity_buf, "identity (I)");
  assertIsBuffer(password_buf, "password (P)");
  assertIsBuffer(secret1_buf, "secret1");
  this._private = { params: params,
                    k_num: getk(params),
                    x_num: getx(params, salt_buf, identity_buf, password_buf),
                    a_num: new BigInteger(secret1_buf),
                    u_buf: identity_buf,
                    s_buf: salt_buf };
  this._private.A_buf = getA(params, this._private.a_num);
}

Client.prototype = {
  computeA: function computeA() {
    return this._private.A_buf;
  },
  setB: function setB(B_buf) {
    var p = this._private;
    var B_num = new BigInteger(B_buf);
    var u_num = getu(p.params, p.A_buf, B_buf);
    var S_buf_x = client_getS(p.params, p.k_num, p.x_num, p.a_num, B_num, u_num);
    p.K_buf = getK(p.params, S_buf_x);
    p.u_num = u_num; // only for tests
    p.S_buf = S_buf_x; // only for tests
    p.B_buf = B_buf;
    p.M1_buf = getM1(p.params, p.u_buf, p.s_buf, p.A_buf, p.B_buf, p.K_buf);
    p.M2_buf = getM2(p.params, p.A_buf, p.M1_buf, p.K_buf);
  },
  computeM1: function computeM1() {
    if (this._private.M1_buf === undefined)
      throw new Error("incomplete protocol");
    return this._private.M1_buf;
  },
  checkM2: function checkM2(serverM2_buf) {
    if (!equal(this._private.M2_buf, serverM2_buf))
      throw new Error("server is not authentic");
  },
  computeK: function computeK() {
    if (this._private.K_buf === undefined)
      throw new Error("incomplete protocol");
    return this._private.K_buf;
  }
};

function Server(params, salt_buf, identity_buf, password_buf, secret2_buf) {
  if (!(this instanceof Server))  {
    return new Server(params, salt_buf, identity_buf, password_buf, secret2_buf);
  }
  assertIsBuffer(salt_buf, "salt (salt)");
  assertIsBuffer(identity_buf, "identity (I)");
  assertIsBuffer(password_buf, "password (P)");
  assertIsBuffer(secret2_buf, "secret2");
  this._private = { params: params,
                    k_num: getk(params),
                    b_num: new BigInteger(secret2_buf),
                    v_num: new BigInteger(computeVerifier(params, salt_buf, identity_buf, password_buf)),
                    u_buf: identity_buf,
                    s_buf: salt_buf };

  this._private.B_buf = getB(params, this._private.k_num,
                             this._private.v_num, this._private.b_num);
}

Server.prototype = {
  computeB: function computeB() {
    return this._private.B_buf;
  },
  setA: function setA(A_buf) {
    var p = this._private;
    var A_num = new BigInteger(A_buf);
    var u_num = getu(p.params, A_buf, p.B_buf);
    var S_buf = server_getS(p.params, p.v_num, A_num, p.b_num, u_num);
    p.K_buf = getK(p.params, S_buf);
    p.M1_buf = getM1(p.params, p.u_buf, p.s_buf, A_buf, p.B_buf, p.K_buf);
    p.M2_buf = getM2(p.params, A_buf, p.M1_buf, p.K_buf);
    p.u_num = u_num; // only for tests
    p.S_buf = S_buf; // only for tests
  },
  checkM1: function checkM1(clientM1_buf) {
    if (this._private.M1_buf === undefined)
      throw new Error("incomplete protocol");
    if (!equal(this._private.M1_buf, clientM1_buf))
      throw new Error("client did not use the same password");
  },
  computeK: function computeK() {
    if (this._private.K_buf === undefined)
      throw new Error("incomplete protocol");
    return this._private.K_buf;
  },
  computeM2: function computeM2() {
    if (this._private.M2_buf === undefined)
      throw new Error("incomplete protocol");
    return this._private.M2_buf;
  }
};

module.exports = {
  params: require('./params'),
  genKey: genKey,
  computeVerifier: computeVerifier,
  Client: Client,
  Server: Server
};
