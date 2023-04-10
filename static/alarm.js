const alarmSubmit = document.getElementById('alarmSubmit');

alarmSubmit.addEventListener('click', setAlarm);



function showNotification(){
  const notification = new Notification(" Payment Remaining ", {body:" Your payment is remaining "});
}

console.log(Notification.permission);

if(Notification.permission !== "denied"){
  Notification.requestPermission().then(permission =>{
      if(permission === "granted"){
           showNotification();
       }
       alert(" Permission  Granted ")
      console.log(permission);
  });
} 

function setAlarm(e) {
    e.preventDefault();
    const alarm = document.getElementById('alarm');
    alarmDate = new Date(alarm.value);
    console.log(`Setting Alarm for ${alarmDate}...`);
    now = new Date();

    let timeToAlarm = alarmDate - now;
    console.log(timeToAlarm);
    if(timeToAlarm>=0){
        setTimeout(() => {
            console.log("Ringing now")
            showNotification();
        }, timeToAlarm);
    }
}