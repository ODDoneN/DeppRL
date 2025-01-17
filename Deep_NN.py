# -*- coding: utf-8 -*-
"""
Created on Sat Sep 28 15:09:29 2019

@author: Ithan
"""
import pandas as pd
import random
import pickle
import tensorflow as tf
import numpy as np
import time as tim
from Simulador import Simulador as simu 
from tensorflow.python.keras import optimizers
from tensorflow.python.keras.models import Sequential, load_model
from tensorflow.python.keras.layers import Flatten, Dense
from tensorflow.python.keras.layers import  Convolution2D, MaxPooling2D
from tensorflow.python.keras import backend as K
from collections import deque 
import matplotlib.pyplot as plt
K.clear_session()
sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(log_device_placement=True)) #el javier usa este comando
#sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))

class Deep_NN:
    def __init__(self, aprendizaje=0.001, epsilon=1, cantidad_acciones=4, estado=np.array([])):
        self.aprendizaje = aprendizaje
        self.epsilon = epsilon # exploracion inicial
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.9995
        self.gamma = 0.9 #0.4
        self.estado=estado #imagen de entrada matriz
        self.memory = deque(maxlen=20000)
        #self.buenos_recuerdos = deque(maxlen=2000)
        self.cantidad_acciones = cantidad_acciones # numero de acciones posibles  
        self.longitud=64
        self.altura = 64
        self.tamano_filtro1 = (8, 8)
        self.tamano_filtro2 = (4, 4)
        self.tamano_filtro3 = (2, 2)
        
        self.filtrosConv1 = 4
        self.filtrosConv2 = 8
        self.filtrosConv3 = 16
        self.tamano_pool = (2, 2)
        self.episodios= 301
        self.modelo=self.contruModelo()
    
    def contruModelo (self):
        cnn = Sequential()
        cnn.add(Convolution2D(self.filtrosConv1, self.tamano_filtro1, padding ="same", input_shape=(self.altura,self.longitud, 3), activation='relu'))
        cnn.add(MaxPooling2D(pool_size=self.tamano_pool))

        cnn.add(Convolution2D(self.filtrosConv2, self.tamano_filtro2, padding ="same",activation='relu'))
        cnn.add(MaxPooling2D(pool_size=self.tamano_pool))
        
        cnn.add(Convolution2D(self.filtrosConv3, self.tamano_filtro3, padding ="same",activation='relu'))
        cnn.add(MaxPooling2D(pool_size=self.tamano_pool))
        
        cnn.add(Flatten())
        #cnn.add(Dense(16,activation='relu'))
        cnn.add(Dense(256, activation='relu'))#sigmoidal--- lineal
        cnn.add(Dense(self.cantidad_acciones,activation='softmax'))#tanh
        
        cnn.compile(loss='mse', optimizer=optimizers.RMSprop(lr=self.aprendizaje))
        return cnn
    def experiencia(self, estado, accion, recompensa, estado_siguiente, logrado):
        self.memory.append((estado, accion, recompensa, estado_siguiente, logrado))

    def decision(self, estado): #toma una accion sea random o la mayor
        valores = self.modelo.predict(estado)
        if np.random.rand() <= self.epsilon:
            x=[random.random(), random.random(), random.random(), random.random()]
            
            return x, valores[0]
        #valores = self.modelo.predict(estado)

        #print (valores[0])
        #print (np.argmax(valores[0]))
        return valores[0], valores[0] # accion random o mayor
       
    def entrenar(self, batch_size, memo):
        miniBatch = random.sample(self.memory, batch_size)#con lo guardado se entrena la red con experiencias random
        #miniBatch = random.sample(agente.memory, batch_size)
        estados = np.zeros((batch_size, 64, 64, 3))

        est_sig = np.zeros((batch_size, 64, 64, 3))
        acciones, recompensas, logrados = [], [], []

        for i in range(batch_size):
            estados[i] = miniBatch[i][0]
            acciones.append(miniBatch[i][1])
            recompensas.append(miniBatch[i][2])
            est_sig[i] = miniBatch[i][3]
            logrados.append(miniBatch[i][4])

        target = self.modelo.predict(estados)
        #target = agente.modelo.predict(estados)
        target_val = self.modelo.predict(est_sig)
        #target_val = agente.modelo.predict(est_sig)
        for x in range(batch_size):      
            if logrados[x]:
                target[x][acciones[x]]=recompensas[x]
                #target[2][acciones[0]]=recompensas[0]
            else:
                target[x][acciones[x]]= (recompensas[x] + self.gamma *
                          np.amax(target_val[x]))
                #target[x][acciones[x]]= (recompensas[x] + agente.gamma *np.amax(target_val[x]))
        # and do the model fit!
        self.modelo.fit(estados, target,
                       epochs=1, verbose=0)        
        #fit_generator([estados,target], epochs=1,verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def cargar_modelo(self, name):
        self.modelo=load_model('modelo_'+name)
        self.modelo.load_weights('pesos_'+name)

    def guardar_modelo(self, name):
        self.modelo.save('modelo_'+name)
        self.modelo.save_weights('pesos_'+name)
        
    def cargar_memoria(self, name):
       file=open("DNN-interactive-humano/"+name,'rb')  #file object in binary read mode
       data=pickle.load(file)      #load the data back
       file.close()
       self.memory=data
       #print(data)
    def pSuccess(Q, reward, gamma):
        n = np.log(Q/reward)/np.log(gamma) #corresponde a Eq. 6 del paper. Python no tiene logaritmo en base gamma, pero por propiedades de logaritmos se puede calcular en base 10 y dividir por el logaritmos de gamma. Es lo mismo, cualquier duda revisar propiedades de logaritmos.
        log10baseGamma = np.log(10)/np.log(gamma) # Es un valor constante. Asumiendo que gamma no cambia. Se ocupa en la linea que viene a continuacion
        probOfSuccess = (n / (2*log10baseGamma)) + 1 #Corresponde a Eq. 7 del paper. Sin considerar la parte estocastica.
        probOfSuccessLimit = np.minimum(1,np.maximum(0,probOfSuccess)) #Corresponde a Eq. 9 del paper. Lo mismo anterior, solo que limita la probabilidad a valores entre 0 y 1.
        #probOfSuccessLimit = probOfSuccessLimit * (1 - stochasticity) #Usar solo si usamos transiciones estocasticas o el parametro sigma
        return probOfSuccessLimit
if __name__ == "__main__":
    
  
    
    sim = simu()
    """
    a=sim.seleccion(0)
    a=sim.seleccion(1)
    a=sim.seleccion(2)
    a=sim.seleccion(3)
   
    sim.restartScenario()
    
    
    #print(len(posiciones))
    sim.tomarObjeto('m_Sphere')           
    #dere
    sim.moverLados('m_Sphere','customizableTable_tableTop#0')  
    #izq
    sim.moverLados('m_Sphere','customizableTable_tableTop#1')  
    #soltar
    sim.soltarObjeto('m_Sphere')
    #casa
    sim.volverCasa()
    
    sim.completado()
    sim.enMesa()
    sim.obtenerPos()
    sim.posEnMesa()
    sim.quedaAlgo()
    sim.objetoTomado()
    sim.restartScenario()    
    print(agente.modelo.predict(state))
    """
    state=sim.kinectVisionRGB()
    agente = Deep_NN(estado=state) 


    #agente.modelo.summary()
    done = False
    batch_size = 128
    times=[]
    recom=[]
    QS1=[]
    QS2=[]
    QS3=[]
    QS4=[]
    es=[]
    rewardCum=0
    timer=0
    timercum=0
    x=0
    """
    while len(agente.memory) <1000:
        action = agente.decision(state)[0]            
        next_state, reward, done = sim.seleccion(action) # segun la accion retorna desde el entorno todo eso
        
        if reward==-0.01 and timer>18:
            reward=reward*(timer-18)
        elif reward==-0.01:
            reward=0
        
        rewardCum=reward+rewardCum
        agente.experiencia(state, action, reward, next_state, done)              
        state = next_state
        
        if done or timer>100:
                timercum=timer+timercum
                print(" score: ",round(rewardCum,2)," time : ",timer," timeTotal : ",timercum)#                      
                sim.restartScenario()
                rewardCum=0
                timer=0
        timer=timer+1
    
    timercum=0
    """
    while x<2:
        agente.cargar_memoria("1000 pasos")
        for e in range(agente.episodios):
            
            state = sim.kinectVisionRGB()# reseteo el estaado y le entrego la imagen nuevamente
            rewardCum=0
            time=0
            
            while True:
                Qvalue= agente.decision(state)#int(input("accion = "))
                if time==0:
                    Q=Qvalue[1]  
                action = np.argmax(Qvalue[0])
                #print(Qvalue[1])            
                next_state, reward, done= sim.seleccion(action) # segun la accion retorna desde el entorno todo eso
                if reward==-0.01 and time>18:
                    reward=reward*(time-18)
                elif reward==-0.01:
                    reward=0
                agente.experiencia(state, action, reward, next_state, done)          
                
                state = next_state
                
                rewardCum=reward+rewardCum
                
                if done or time>100:
                    timercum=time+timercum
                    times.append(time)
                    recom.append(round(rewardCum,2))
                    es.append(e)
                    QS1.append(Q[0])
                    QS2.append(Q[1])
                    QS3.append(Q[2])
                    QS4.append(Q[3])
                    print(x,"episode: ",e," score: ",round(rewardCum,2)," e : ",agente.epsilon," time ",time ," timeTotal : ",timercum)#
                    
                    break
                    
                if len(agente.memory) >= batch_size:
                    agente.entrenar(batch_size,agente.memory)     
                                
                time=time+1

            if e> 299:
                #agente.guardar_modelo("DNN-interactive-maestro"+str(x))
                #print(Q)
                data={'recom':recom,'times':times, 'ValorQ1':QS1,'ValorQ2':QS2,'ValorQ3':QS3,'ValorQ4':QS4}
                df = pd.DataFrame(data, columns = ['recom', 'times','ValorQ1','ValorQ2','ValorQ3','ValorQ4'])
                df.to_csv('DNN-interactive-maestro-V2FIN-'+str(x)+'.csv')
                break
            if e%10==0 and e>9:
                     
                plt.plot(es,recom)
                plt.show()
                #plt.plot(es,pSuccess(QS1, recom, 0.9),pSuccess(QS2, recom, 0.9),pSuccess(QS3, recom, 0.9),pSuccess(QS4, recom, 0.9))
                #plt.show()
            sim.restartScenario()
            tim.sleep(1)
            
        agente.epsilon=1
        state=sim.kinectVisionRGB()
        agente = Deep_NN(estado=state)     
        #agente.modelo.summary()
        done = False
        terminado = 0 
        batch_size = 128
        times=[]
        recom=[]
        es=[]
        QS1=[]
        QS2=[]
        QS3=[]
        QS4=[]
        rewardCum=0
        timer=0
        timercum=0
        x=x+1
    
    """            
    #plt.plot(times,recom) 
    #plt.show()               
    plt.plot(es,recom)
    plt.show()
    plt.plot(es,times)
    plt.show()           
    agente.guardar_modelo("Maestro2")   
    

   
    data={'recom':recom,'times':times}
    df = pd.DataFrame(data, columns = ['recom', 'times'])
    df.to_csv('maestro2.csv')
    

    
    next_state, reward, done= sim.seleccion(2) # segun la accion retorna desde el entorno todo eso    
    tar=agente.modelo.predict(next_state)
    tar[0][0]=0
    tar[0][1]=1
    tar[0][2]=0
    tar[0][3]=0
    for x in range(1000):
        his=agente.modelo.fit(next_state,tar,epochs=1, verbose=0)
    
    type(his)
    plt.figure(0)  
    plt.plot(his.history['acc'],'r')  
    plt.plot(his.history['val_acc'],'g')  
    plt.xticks(np.arange(0, 11, 2.0))  
    plt.rcParams['figure.figsize'] = (8, 6)  
    plt.xlabel("Numero de Epocas")  
    plt.ylabel("Precisión")  
    plt.title("Precisión de entrenamiento vs Precisión de Validación")  
    plt.legend(['entrenamiento','Validación'])
    
    """
         #if e % 10 == 0:
          #   agent.save("./save/cartpole-dqn.h5")
        #agente.guardar_modelo("6 figuras javier")
    #agente.cargar_modelo("uno")
"""     
        time=0
        e=1
        ee=0.9993
        while True:
            time=time+1
            if e > 0.01:
                e *= ee
            else:
                print(time)
                break
                
"""     
