import React, { useState, setState } from 'react';
import logo from './static/construction.png';
import axios from 'axios';
import Container from './container';
import './Home.css';

// will house items, short summary and all other information made available via the MongoDB instance

function Trips() {
    let [trips, setTrips]= React.useState(0)
    function handleData(){
        axios.get(`/get_items?type=trips`).then((response)=> {
            if (trips==0){
                setTrips(response.data)
            }
        })
    }
    handleData()
    console.log('Trips', trips)
    return (
        <div className="App">
          <header className="App-header">
          {Object.entries(trips).map((d, i)=>{
            return <ul><li>{d[0]}</li> <li>{d[1]}</li></ul>
          })}
          </header>
          
        </div>
      );
    
  }
  
  export default Trips;
  