from sympy import *
import os
import time

TWO_POW_32 = 4294967296

def get_random_int(nbytes):
    return int.from_bytes(os.urandom(nbytes), byteorder="big")

# USE RSA PSRBG to generate sequence of 512 pseudorandom bis each second
# t=time in epoch (seconds since 00:00:00 01/01/1970)
# n = p*q where p and q are secret randomly chosen 1024 bit primes
# lam = lambda(n) = (p-1)*(q-12)/gcd(p-1,q-1) is Carmichael Lambda Totient
# e is exponent coprime to lam
# p and q are reset once per minute
# x0 is secret randomly chosen seed less than n
# xt=pow(x0,pow(e,M*t,lam),n) is the secret pseudorandom number for time
#     where is M=2**20 so the generator jumps about one million steps ahead each second
# zt = Sum[2**k (pow(xt,pow(e,k,lam),n) mod 2),{k,0,511}] is publicly displayed
#     512-bit  pseudorandom number for time t
#  note only one bit of each RSA pseudorandom number is used in calculation of zt
# hash(zt) is shorter number derived from zt
# hash of zt for NEXT second is displayed at time t
#
# ideally x0 has provably maximum order=lambda(n) modulo n,
#     and e has provably large order modulo lambda(n).
#  this requires more complicated determination of primes

class SimpleRSARNG:
    def __init__(self, nbits = 2048, e = 3):

        # calculate initial parameters p, q, lambda, etc
        self.e = int(e)
        self.nbits = int(nbits)
        self.nbytes = nbits//8
        self.nbitsprime = nbits//2
        self.nbytesprime = self.nbitsprime//8
        self.t = int(time.time())
        self.reset_primes()

    def reset_primes(self):
        """
        choose 2048 bit composite n=p*q
        choose two 1024 bit primes p and q without any special properties or checks other than
        the exponent e must be coprime to phi(n) by requiring gcd(e,p-1)=gcd(e,q-1)=1
        """
        nbitsprime = self.nbitsprime
        nbytesprime = self.nbytesprime
        nbytes = self.nbytes
        e = self.e

        p=get_random_int(nbytesprime)
        twonprimebitsminus1=pow(2, nbitsprime - 1)
        while p < twonprimebitsminus1:
        	p = 2 * p

        p = nextprime(p)
        while igcd(e, p - 1) != 1:
        	p = nextprime(p)

        q = get_random_int(nbytesprime)
        while q < twonprimebitsminus1:
        	q = 2 * q

        q = nextprime(q)
        while igcd(e, q - 1) != 1:
        	q = nextprime(q)

        n = p * q
        lam = (p - 1) * (q - 1) // igcd(p - 1, q - 1)
        x0 = get_random_int(nbytes - 1)

        self.n = n
        self.lam = lam
        self.x0 = x0

    def get_rng(self):
        M=1048576 # 2**20
        N=512

        self.t += 1

        t = self.t
        x0 = self.x0
        e = self.e
        n = self.n
        lam = self.lam

        xt = pow(x0, pow(e, M * t, lam), n)
        zt = 0
        twok = 1
        x = xt
        for k in range(0, N):
            zt = zt + twok * (x&1)
            x = pow(x, e, n)
            twok = twok << 1

        return zt
