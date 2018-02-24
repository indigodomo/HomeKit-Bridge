## SRP Protocol Design

SRP is the newest addition to a new class of strong authentication
protocols that resist all the well-known passive and active attacks
over the network.
SRP borrows some elements from other key-exchange and
identification protocols and adds some subtle modifications and
refinements.
The result is a protocol that preserves the strength and
efficiency of the EKE family protocols while fixing some of
their shortcomings.

The following is a description of SRP-6 and 6a, the latest versions of SRP:

```
  N    A large safe prime (N = 2q+1, where q is prime)
       All arithmetic is done modulo N.
  g    A generator modulo N
  k    Multiplier parameter (k = H(N, g) in SRP-6a, k = 3 for legacy SRP-6)
  s    User's salt
  I    Username
  p    Cleartext Password
  H()  One-way hash function
  ^    (Modular) Exponentiation
  u    Random scrambling parameter
  a,b  Secret ephemeral values
  A,B  Public ephemeral values
  x    Private key (derived from p and s)
  v    Password verifier
```

The host stores passwords using the following formula:

```
  x = H(s, p)               (s is chosen randomly)
  v = g^x                   (computes password verifier)
```

The host then keeps {I, s, v} in its password database.

The authentication protocol itself goes as follows:

```
User -> Host:  I, A = g^a                  (identifies self, a = random number)
Host -> User:  s, B = kv + g^b             (sends salt, b = random number)

        Both:  u = H(A, B)

        User:  x = H(s, p)                 (user enters password)
        User:  S = (B - kg^x) ^ (a + ux)   (computes session key)
        User:  K = H(S)

        Host:  S = (Av^u) ^ b              (computes session key)
        Host:  K = H(S)
```

Now the two parties have a shared, strong session key K.  To complete
authentication, they need to prove to each other that their keys match.
One possible way:

```
User -> Host:  M = H(H(N) xor H(g), H(I), s, A, B, K)
Host -> User:  H(A, M, K)
```

The two parties also employ the following safeguards:

* The user will abort if he receives B == 0 (mod N) or u == 0.
* The host will abort if it detects that A == 0 (mod N).
* The user must show his proof of K first.  If the server detects that
the user's proof is incorrect, it must abort without showing its own
proof of K.


A [paper](http://srp.stanford.edu/srp6.ps) describing this protocol is also
available, as well as a
[conference paper](ftp://srp.stanford.edu/pub/srp/srp.ps)
describing an older version of the protocol.

For historical interest, descriptions of the
previous versions of SRP are available on this site:

* [SRP-1](http://srp.stanford.edu/design1.html)
* [SRP-2](http://srp.stanford.edu/design2.html)
* [SRP-3](http://srp.stanford.edu/design3.html)

This document has been copied from [http://srp.stanford.edu/design.html](http://srp.stanford.edu/design.html)
