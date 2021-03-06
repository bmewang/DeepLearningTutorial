#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Maziar Raissi
"""

import autograd.numpy as np
from autograd import value_and_grad
from Utilities import fetch_minibatch_rnn, stochastic_update_Adam, activation

class RecurrentNeuralNetworks:
    
    def __init__(self, X, Y, hidden_dim, 
                 max_iter = 2000, N_batch = 1, monitor_likelihood = 10, lrate = 1e-3):
        
        # X has the form lags x data x dim
        # Y has the form data x dim
        
        self.X = X
        self.Y = Y
        self.X_dim = X.shape[-1]
        self.Y_dim = Y.shape[-1]
        self.hidden_dim = hidden_dim
        self.lags = X.shape[0]
        
        self.max_iter = max_iter
        self.N_batch = N_batch
        self.monitor_likelihood = monitor_likelihood
        
        self.hyp = self.initialize_RNN()
        
        # Adam optimizer parameters
        self.mt_hyp = np.zeros(self.hyp.shape)
        self.vt_hyp = np.zeros(self.hyp.shape)
        self.lrate = lrate
        
        print("Total number of parameters: %d" % (self.hyp.shape[0]))  
        
    def initialize_RNN(self):
        hyp = np.array([])
        Q = self.hidden_dim
            
        U = -np.sqrt(6.0/(self.X_dim+Q)) + 2.0*np.sqrt(6.0/(self.X_dim+Q))*np.random.rand(self.X_dim,Q)
        b = np.zeros((1,Q))
        W = np.eye(Q)
        hyp = np.concatenate([hyp, U.ravel(), b.ravel(), W.ravel()])            
        
        V = -np.sqrt(6.0/(Q+self.Y_dim)) + 2.0*np.sqrt(6.0/(Q+self.Y_dim))*np.random.rand(Q,self.Y_dim)
        c = np.zeros((1,self.Y_dim))
        hyp = np.concatenate([hyp, V.ravel(), c.ravel()])
    
        return hyp
        
    def forward_pass(self, X, hyp):     
        Q = self.hidden_dim
        H = np.zeros((X.shape[1],Q))
        
        idx_1 = 0
        idx_2 = idx_1 + self.X_dim*Q
        idx_3 = idx_2 + Q
        idx_4 = idx_3 + Q*Q
        U = np.reshape(hyp[idx_1:idx_2], (self.X_dim,Q))
        b = np.reshape(hyp[idx_2:idx_3], (1,Q))
        W = np.reshape(hyp[idx_3:idx_4], (Q,Q))
        
        for i in range(0, self.lags):
            H = activation(np.matmul(H,W) + np.matmul(X[i,:,:],U) + b)
                
        idx_1 = idx_4
        idx_2 = idx_1 + Q*self.Y_dim
        idx_3 = idx_2 + self.Y_dim
        V = np.reshape(hyp[idx_1:idx_2], (Q,self.Y_dim))
        c = np.reshape(hyp[idx_2:idx_3], (1,self.Y_dim))
        Y = np.matmul(H,V) + c
        
        return Y
    
    
    def MSE(self, hyp):
        X = self.X_batch
        Y = self.Y_batch                          
        Y_star = self.forward_pass(X, hyp)                
        return np.mean((Y-Y_star)**2)
    
    def train(self):
        
        # Gradients from autograd 
        MSE = value_and_grad(self.MSE)
        
        for i in range(1,self.max_iter+1):
            # Fetch minibatch
            self.X_batch, self.Y_batch = fetch_minibatch_rnn(self.X, self.Y, self.N_batch)
            
            # Compute likelihood_UB and gradients 
            MSE_value, D_MSE = MSE(self.hyp)
            
            # Update hyper-parameters
            self.hyp, self.mt_hyp, self.vt_hyp = stochastic_update_Adam(self.hyp, D_MSE, self.mt_hyp, self.vt_hyp, self.lrate, i)
            
            if i % self.monitor_likelihood == 0:
                print("Iteration: %d, MSE: %.5e" % (i, MSE_value))
    
        
        