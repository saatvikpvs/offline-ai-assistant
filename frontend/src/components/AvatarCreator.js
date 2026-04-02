import React from "react";

export default function AvatarCreator({setAvatar}) {

const url = "https://demo.readyplayer.me/avatar?frameApi";

window.addEventListener("message",(event)=>{

if(event.data?.source==="readyplayerme"){

if(event.data.eventName==="v1.avatar.exported"){

setAvatar(event.data.data.url);

}

}

});

return (

<iframe
title="Avatar Creator"
src={url}
style={{
width:"100%",
height:"600px",
border:"none"
}}
/>

);

}