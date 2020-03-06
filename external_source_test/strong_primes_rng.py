from sympy import *
import os
import time

def get_random_int(nbytes):
    return int.from_bytes(os.urandom(nbytes), byteorder="big")

#choose nbits long strong prime p such that:
#    p=2*a1*p1+1
#    p1=2*a2*p2+1
#    such that:
#    phi(p)=2*a1*p1
#    phi(phi(p))=phi(2*a1)*a2*a2*p2
#    a1 small enough so we can calculate its prime factors and totient
#    so we can ensure exponent e has large multiplicative order modulo phi(n)
#    and so that we can ensure that x0 has maximum multiplicative order modulo n
#    of lambda(n) = (p-1)*(q-1)/gcd(p-1,q-1)
#  return values are list [p,p1,a1]
def RSAStrongPrime(nbits,e):

	nbytes=nbits//8
	p=get_random_int(nbytes)
	while p<2**(nbits-1):
		p = 2*p
	#print "p=",p

	p2=nextprime(get_random_int(nbytes//2))
	#print "p2=",p2

	nbytesa1=nbytes//4
	while nbytesa1 > 10:
		nbytesa1 -= 1
	a1=get_random_int(nbytesa1)
	p1=p//(2*a1)
	a2=(p1-1)//(2*p2)
	p1=2*a2*p2+1
	while not isprime(p1):
		a2=a2+1
		p1=2*a2*p2+1
	#print "p1=",p1


	a1=(p-1)//(2*p1)
	finished=False
	while not finished:
		a1=a1-1
		if gcd(e,2*a1)==1:
			p=2*a1*p1+1
			if isprime(p):
				phi=p-1
				phiphi=totient(2*a1)*(p1-1)
				#print "gcd(e,phi)=",gcd(e,phi)
				#print "phi=",phi
				#print "phiphi=",phiphi
				#print "pow(e,phiphi,phi)=",pow(e,phiphi,phi)
				#print "pow(e,phiphi/p2,phi)=",pow(e,phiphi/p2,phi)
				if pow(e,phiphi//p2,phi)!=1:
					pplus1=p+1
					pp=1
					for i in range(0,82025):
						pp=nextprime(pp)
						while pplus1%pp==0:
							pplus1 = pplus1//pp
					#print "pplus1 after prime factors less than 2^20 removed=",pplus1
					if pplus1 > pow(2,nbits//2):
						finished=True
	phip=p-1
	phifactors=factorint(2*a1)
	phifactors[p1]=1
	#print "p=",p
	#print "phi(p)=",phi
	#print "phi(phi(p))=",phiphi
	#print "phifactors=",phifactors
	#print "p1=",p1
	#print "p2=",p2
	#print "a1=",a1
	#print "a2=",a2

	return [p,p1,a1];

import time
start = time.perf_counter()
prime = RSAStrongPrime(1028, 3)
print(prime)
print('took {}'.format(time.perf_counter() - start))
