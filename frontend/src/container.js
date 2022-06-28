import React, { useState, setState } from 'react';
import './Home.css';
import krolo from './static/krogerLogo.svg'

export default function Container(){
    let y=0
    return(
    <div className="showcase">
    {y===0  && <img src={krolo}></img>}
        <h1>Item Container</h1>
    
    </div>)
}