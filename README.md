# Secure-Voting-Platform-Demo
security requirements for the Electronic Voting Platform

Voting-Specific Security Requirements
System shall ensure regrtered voters can access the platform
Read only audi log - System
30 min time out after 3 fialed login attemts
Session time out after 5 min
Code documentation and Review in Commits
//IP blacklisting
//E2E between vote transmission
Hashing and Salting
Captcha
//SMS with Security(User parameter cryptosystem)
RBAC
DB role restriction

Development-Specific Security Requirements
Not storing passwords in code 
//Firewall -- Docker Network Setup for firewall
Multi voting diablility - One vote for each election
// Devops pipleline - Unit testcases & Static Code analysis for <vulnablities >https://hashcat.net/cap2hashcat/index.pland secrects
// SKS - RSA key security
