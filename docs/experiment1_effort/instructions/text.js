var height = 443;
var height_e = 298;
// 2em + height of trial images
// jspsych font 1em = 18px

var page_starter = '<div style="height:' + height + 'px; text-align: center;">';
var page_starter_e = '<div style="height:' + height_e + 'px; text-align: center;">';

var page1 = page_starter +
        '<div style="width: 30%; margin-left: 20%; float:left;">' +
        '<img src="instructions/agent_red.png" style="width: 60px;' +
            'margin-top: 12em;"></img> </div>' +
        '<div style="width: 30%; margin-right: 20%; float:left;">' +
        '<img src="instructions/agent_blue.png" style="width: 60px;' +
            'margin-top: 12em;"></img> </div> </div>' + 
        '<p> In this experiment, you will watch a red player and a blue' +
        ' player moving around in different grids. </p>';

var page2 = page_starter + 
        '<img src="instructions/instructions1.gif" style="margin-top: 2em;">' +
        ' </img> </div>' +
        '<p> The goal of the red player is to reach the star before time runs' +
        ' out. On each step, the red player can move up, down, left, right,' +
        ' or stay in place. They cannot move through walls. If they reach' +
        ' the star in time, then they succeed! </p>';

var page3 = page_starter + 
        '<img src="instructions/instructions2.gif" style="margin-top: 2em;">' +
        ' </img> </div>' +
        '<p> Similarly, the blue player can move up, down, left, right, or' +
        ' stay in place, and cannot move through walls. Some of the' +
        ' grids contain boxes. The blue player can additionally push or' +
        ' pull any of these boxes around. </p>';

var page4 = page_starter_e +
        '<img src="instructions/instructions3.gif" style="height: 160px; margin:' +
        ' auto; margin-top: 4em;"> </div>' +
        '<p> Neither player can move through boxes.' +
        // double quotes
        " Sometimes the blue player's actions help the red player reach" +
        ' the star, and sometimes they hinder the red player from' +
        ' reaching the star. <br> <br> Here is an example of the blue' +
        ' player <b>helping</b> the red player. </p>';

var page5 = page_starter_e +
        '<img src="instructions/instructions4.gif" style="height: 160px; margin:' +
        ' auto; margin-top: 4em;"> </div> <p> Here is an example of the' +
        ' blue player <b>hindering</b> the red player. </p>';

var page6 = page_starter_e + 
        '<h2> Example </h2> <img src="trials/E/00.png" style="max-height: 100%;' +
        ' width: auto;"> </img> </div>' +
        '<p> Here is an example grid. The red player has 8 timesteps to reach the' +
        ' star. The number of timesteps remaining is shown on the right.' +
        '<br> <br> Click the "Next" button to see what happens next. </p>';

var page7 = page_starter_e + 
        '<h2> Example </h2> <img src="trials/E/01.png" style="max-height: 100%;' +
        ' width: auto;"> </img> </div>' +
        '<p> Both players take a step right. The blue player picks up the box' +
        ' to their right. </p>';

var page8 = page_starter_e +
        '<h2> Example </h2> <img src="trials/E/02.png" style="max-height: 100%;' +
        ' width: auto;"> </img> </div>' +
        '<p> The red player takes another step right. The blue player pulls the' +
        ' box to the left. </p>';

var page9 = page_starter_e + 
        '<h2> Example </h2> <img src="trials/E/03.png" style="max-height: 100%;' +
        ' width: auto;"> </img> </div>' +
        '<p> The red player takes a step down, and the blue player lets go of' +
        ' the box. </p>';

var page10 = page_starter_e + 
        '<h2> Example </h2> <img src="trials/E/04.png" style="max-height: 100%;' +
        ' width: auto;"> </img> </div>' +
        '<p> The red player takes another step down. </p>';

var page11 = page_starter_e + 
        '<h2> Example </h2> <img src="trials/E/05.png" style="max-height: 100%;' +
        ' width: auto;"> </img> </div>' +
        '<p> The red player takes a step right. </p>';

var page12 = page_starter_e + 
        '<h2> Example </h2> <img src="trials/E/06.png" style="max-height: 100%;' +
        ' width: auto;"> </img> </div>' +
        '<p> The red player takes a step up and reaches the star. </p>';

var page13 = page_starter_e + 
        '<h2> Example </h2> <img src="trials/E/07.png" style="max-height: 100%;' +
        ' width: auto;"> </img> </div>' +
        '<p> The red player succeeded this time! And there were 2 timesteps remaining.' +
        ' </p> <p> Next, we will ask you some questions about what happened.' +
        ' You will be able to watch a video replay of what happened. </p>';

var instruction_pages = [
    page1,
    page2,
    page3,
    page4,
    page5,
    page6,
    page7,
    page8,
    page9,
    page10,
    page11,
    page12,
    page13
];

for (var i = 0; i < instruction_pages.length; i++) {
    instruction_pages[i] = '<div style="width: 700px; min-width: 300px; margin:' +
        'auto 5em;">' + instruction_pages[i] + '</div>';
}

var instructions_last = '<p> In this experiment, we will show you scenarios' +
        ' like this where the red player either succeeds or fails to reach' +
        ' the star in time. We want to know how much effort you think the' +
        ' blue player exerted each time.</p>';

var comprehension1 = '<p> The goal of both players is to reach the star first.</p>';
var options1 = ['True', 'False']
                    
var comprehension2 = '<p> Which of the following is possible here? </p>' +
        '<img src="instructions/comprehension1.png" style="height: auto;' +
        ' width: 50%;"></img> <br> <ol>' +
        '<li> The red player can walk around the box. </li>' +
        '<li> The red player can push the box out of the way. </li>' +
        // double quotes
        "<li> The blue player can pull the box out of the red player's way." +
        '</li> </ol>';
var options2 = ['1 only', '2 only', '3 only', 'All of the above'];

var comprehension3 = '<p> The blue player can either help or hinder the red' +
        ' player using the boxes. </p>';
var options3 = ['True', 'False'];
                    
var start_prompt1 = '<p> Correct! You will now see 24 different scenarios featuring' +
        ' a red player and a blue player in a different grid each time. </p>' +
        '<p> In each scenario, you will first get to walk through a step' +
        '-by-step play of what happened. You can proceed by either clicking' +
        ' the buttons or pressing arrow keys. You can go both forwards and' +
        ' backwards to see what happened on each time step. Then, you will see' +
        ' a video replay of what happened while answering the question, just' +
        ' like in the example. </p>';

var start_prompt2 = '<p> Remember, the goal of the red player is to reach the star' +
        ' before time runs out, and the blue player can move boxes around.' +
        ' Neither player can walk through boxes or walls. </p>' +
        ' <p> Please do not refresh the page. Click the start button whenever' +
        ' you are ready. <p>';

var instruction_images = [
        'instructions/agent_red.png',
        'instructions/agent_blue.png',
        'instructions/instructions1.gif',
        'instructions/instructions2.gif',
        'instructions/instructions3.gif',
        'instructions/instructions4.gif',
        'instructions/comprehension1.png',
        'trials/E/00.png',
        'trials/E/01.png',
        'trials/E/02.png',
        'trials/E/03.png',
        'trials/E/04.png',
        'trials/E/05.png',
        'trials/E/06.png',
        'trials/E/07.png',
        'trials/E/full.gif'
];
