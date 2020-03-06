from sympy import *
import os
import binascii
import time

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


# calculate initial parameters p, q, lambda, etc
e=3
nbits=2048
nbytes=nbits//8
nbitsprime=nbits//2
nbytesprime=nbitsprime//8

#choose 2048 bit composite n=p*q
#choose two 1024 bit primes p and q without any special properties or checks other than
# the exponent e must be coprime to phi(n) by requiring gcd(e,p-1)=gcd(e,q-1)=1

print( "initializing primes p and q" )


p=int(binascii.hexlify(os.urandom(nbytesprime)),16)
twonprimebitsminus1=pow(2,nbitsprime-1)
while p<twonprimebitsminus1:
	p = 2*p
p=nextprime(p)
while igcd(e,p-1)!= 1:
	p=nextprime(p)
q=int(binascii.hexlify(os.urandom(nbytesprime)),16)
while q<twonprimebitsminus1:
	q = 2*q
q=nextprime(q)
while igcd(e,q-1)!= 1:
	q=nextprime(q)
n=p*q
lam=(p-1)*(q-1)//igcd(p-1,q-1)
x0=int(binascii.hexlify(os.urandom(nbytes-1)),16)
print( "p=",hex(p) )
print( "q=",hex(q) )
print( "n=",hex(n) )
print( "e=",e )
print( "lam=",hex(lam) )
print( "x0=",hex(x0) )




M=2**20
N=512
print( "setup initial pseudorandom parameters" )
t=int(time.time())
t0=t
xt0=pow(x0,pow(e,M*t0,lam),n)
zt0=0
twok=1
x=xt0
for k in range(0,N):
	zt0=zt0+twok*(x%2)
	x=pow(x,e,n)
	twok=2*twok
ht0=zt0%4294967296

t1=t0+1
xt1=pow(x0,pow(e,M*t1,lam),n)
zt1=0
twok=1
x=xt1
for k in range(0,N):
	zt1=zt1+twok*(x%2)
	x=pow(x,e,n)
	twok=2*twok
ht1=zt1%4294967296


t2=t1+1
xt2=pow(x0,pow(e,M*t2,lam),n)
zt2=0
twok=1
x=xt2
for k in range(0,N):
	zt2=zt2+twok*(x%2)
	x=pow(x,e,n)
	twok=2*twok
ht2=zt2%4294967296


print( "t0=",t0, time.asctime(time.gmtime(t0)) )
print( "xt0=",hex(xt0) )
print( "zt0=",hex(zt0) )
print( "ht0=",hex(ht0) )

print( " " )
print( "t1=",t1, time.asctime(time.gmtime(t1)) )
print( "xt1=",hex(xt1) )
print( "zt1=",hex(zt1) )
print( "ht1=",hex(ht1) )

print( " " )
print( "t2=",t2,time.asctime(time.gmtime(t2)) )
print( "xt2=",hex(xt2) )
print( "zt2=",hex(zt2) )
print( "ht2=",hex(ht2) )
print( " " )

#post t0
print( "t0=",t0, time.asctime(time.gmtime(t0)) )
print( "zt0=",hex(zt0) )
print( "ht1=",hex(ht1) )
starttime=t0

tlastpost=t0

#reset
t0=t1
xt0=xt1
zt0=zt1
ht0=ht1

t1=t2
xt1=xt2
zt1=zt2
ht1=ht2

t2=t1+1
xt2=pow(x0,pow(e,M*t2,lam),n)
zt2=0
twok=1
x=xt2
for k in range(0,N):
	zt2=zt2+twok*(x%2)
	x=pow(x,e,n)
	twok=2*twok
ht2=zt2%4294967296


print( "start broadcasting" )
count=0
t=time.time()
while True:
	t=int(time.time())
	if (t > tlastpost):

		if (t0%3600==0):
			print( " " )
			print( "parameters used during previous hour were:" )
			print( "p=",hex(plast) )
			print( "q=",hex(qlast) )
			print( "n=",hex(nlast) )
			print( "e=",e )
			print( "lam=",hex(lamlast) )
			print( "x0=",hex(x0last) )


		count = count + 1
		#post t0
		print( " " )
		print( "timestamp, UTC time, zt, and lowest four bytes of next zt" )
		print( t0, "  ", time.strftime("%H:%M:%S %m/%d/%Y UTC", time.gmtime(t0)) )
		print( hex(zt0) )
		print( hex(ht1) )

		tlastpost=t0

		t0=t1
		xt0=xt1
		zt0=zt1
		ht0=ht1

		t1=t2
		xt1=xt2
		zt1=zt2
		ht1=ht2


		t2=t1+1
		xt2=pow(x0,pow(e,M*t2,lam),n)
		zt2=0
		twok=1
		x=xt2
		for k in range(0,N):
			zt2=zt2+twok*(x&1)
			x=pow(x,e,n)
			twok=twok<<1
		ht2=zt2%4294967296

		if (t0%3600==3558):
			print( "resetting primes before top of hour" )
			plast=p
			qlast=q
			nlast=n
			lamlast=lam
			x0last=x0
			clock0=time.clock()
			p=int(binascii.hexlify(os.urandom(nbytesprime)),16)
			while p<twonprimebitsminus1:
				p = 2*p
			p=nextprime(p)
			while igcd(e,p-1)!= 1:
				p=nextprime(p)
			q=int(binascii.hexlify(os.urandom(nbytesprime)),16)
			while q<twonprimebitsminus1:
				q = 2*q
			q=nextprime(q)
			while igcd(e,q-1)!= 1:
				q=nextprime(q)
			n=p*q
			lam=(p-1)*(q-1)//igcd(p-1,q-1)
			x0=int(binascii.hexlify(os.urandom(nbytes-1)),16)
			clock1=time.clock()
			print( "time to reset primes =",clock1-clock0 )






print( count )
