var ex_outcome_verb = 'succeed';
var ex_red_name = 'Parker';
var ex_blue_name = 'Kit';
var height = 443;
var height_short = 352;
// 5em + height of trial images
// jspsych font 1em = 18px

var starter = '<div style="height:' + height + 'px; text-align: center;">';
var starter_short = '<div style="height:' + height_short + 'px; text-align: center;">'; 
var starter_ex = starter_short + '<h2> Example </h2> <img src="trials/0/';
var end_ex = '.png" style="max-height: 100%; width: auto;"> </img> <p>' +
        'Players: ' + red(ex_red_name) + ', ' + blue(ex_blue_name) + '</p> </div>';

var page1 = starter +
        '<div style="width: 30%; margin-left: 20%; float:left;">' +
        '<img src="instructions/agent_red.png" style="width: 60px;' +
            'margin-top: 12em;"></img> </div>' +
        '<div style="width: 30%; margin-right: 20%; float:left;">' +
        '<img src="instructions/agent_blue.png" style="width: 60px;' +
            'margin-top: 12em;"></img> </div> </div>' + 
        '<p> In this experiment, you will watch a game that involves' +
        ' a red player and a blue player moving around in different' +
        ' grids. </p>';

var page2 = starter + 
        '<img src="instructions/instructions1.gif" style="margin-top: 2em;">' +
        ' </img> </div>' +
        '<p> The goal of the red player is to reach the star before time runs' +
        ' out. On each step, the red player can move up, down, left, right,' +
        ' or stay in place. They cannot move through walls. If they reach' +
        ' the star in time, then they succeed! </p>';

var page3 = starter + 
        '<img src="instructions/instructions2.gif" style="margin-top: 2em;">' +
        ' </img> </div>' +
        '<p> Similarly, the blue player can move up, down, left, right, or' +
        ' stay in place, and cannot move through walls. Some of the' +
        ' grids contain boxes. The blue player can additionally pick these' +
        ' boxes up to push or pull around. </p>';

var page4 = starter_short +
        '<img src="instructions/instructions3.gif" style="height: 240px; margin:' +
        ' auto; margin-top: 4em;"> </div>' +
        '<p> The two players take turns moving. Neither player can move through boxes.' +
        // double quotes
        " Sometimes the blue player's actions help the red player reach" +
        ' the star, and sometimes they hinder the red player from' +
        ' reaching the star. <br> <br> Here is an example of the red' +
        ' player <b>succeeding</b> in reaching the star. </p>';

var page5 = starter_short +
        '<img src="instructions/instructions4.gif" style="height: 240px; margin:' +
        ' auto; margin-top: 4em;"> </div> <p> Here is an example of the' +
        ' red player <b>failing</b> to reach the star. </p>';

var pageE1 = starter_ex + '00' + end_ex +
        // double quotes
        "<p> Let's watch an example. " + red(ex_red_name) + ' was the red' +
        ' player and ' + blue(ex_blue_name) + ' was the blue player.' +
        ' The number of timesteps remaining is shown on the right.' +
        ' The red player always goes first. <br> <br>' +
        ' Click the "Next" button to see what happened next. </p>';

var pageE2 = starter_ex + '01' + end_ex +
        '<p>' + red(ex_red_name) + ' went first and took a step right. </p>';

var pageE3 = starter_ex + '02' + end_ex +
        '<p>' + blue(ex_blue_name) + ' took a step right. </p>';

var pageE4 = starter_ex + '03' + end_ex +
        '<p>' + red(ex_red_name) + ' took another step right. </p>';

var pageE5 = starter_ex + '04' + end_ex +
        '<p>' + blue(ex_blue_name) + ' picked up the box. </p>';

var pageE6 = starter_ex + '05' + end_ex +
        '<p>' + red(ex_red_name) + ' took a step down. </p>';

var pageE7 = starter_ex + '06' + end_ex +
        '<p>' + blue(ex_blue_name) + ' pulled the box to the left. </p>';

var pageE8 = starter_ex + '07' + end_ex +
        '<p>' + red(ex_red_name) + ' took another step down. </p>';

var pageE9 = starter_ex + '08' + end_ex +
        '<p>' + blue(ex_blue_name) + ' let go of the box. </p>';

var pageE10 = starter_ex + '09' + end_ex +
        '<p>' + red(ex_red_name) + ' took a step right. </p>';

var pageE11 = starter_ex + '10' + end_ex +
        '<p>' + blue(ex_blue_name) + ' did nothing on this timestep. </p>';

var pageE12 = starter_ex + '11' + end_ex +
        '<p>' + red(ex_red_name) + ' took a step up and reached the star. </p>';

var pageE13 = starter_ex + '12' + end_ex +
        '<p>' + red(ex_red_name) + ' succeeded! And there were 2 timesteps remaining.' +
        ' </p> <p> Next, we will ask you some questions about what happened.' +
        ' You will be able to watch a video replay of what happened. </p>';


var instruction_pages = [
    page1,
    page2,
    page3,
    page4,
    page5,
    pageE1,
    pageE2,
    pageE3,
    pageE4,
    pageE5,
    pageE6,
    pageE7,
    pageE8,
    pageE9,
    pageE10,
    pageE11,
    pageE12,
    pageE13
];

for (var i = 0; i < instruction_pages.length; i++) {
    instruction_pages[i] = '<div style="width: 700px; min-width: 300px; margin:' +
        'auto 5em;">' + instruction_pages[i] + '</div>';
}

var instructions_last = '<p> In this experiment, we will show you scenarios' +
        ' like this where the red player either succeeds or fails to reach' +
        ' the star in time. We want to know why you think the red player' +
        ' succeeded or failed in each case. </p>';

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
        ' the buttons, or pressing left (&#8592;) and right (&#8594;) arrow keys.' +
        ' You can go both forwards and backwards to see what happened on' +
        ' each time step. Then, you will see a video replay of what happened' +
        ' while answering the question, just like in the example. </p>';

var start_prompt2 = '<p> Remember, the goal of the ' + red('red player') + ' is to' +
        ' reach the star before time runs out, and the ' + blue('blue player') +
        ' can move boxes around. Neither player can walk through boxes or walls.' +
        '</p> <p> Please do not refresh the page. Click the Start button whenever' +
        // double quotes
        " you're ready. <p>";

var instruction_images = [
        'instructions/agent_red.png',
        'instructions/agent_blue.png',
        'instructions/instructions1.gif',
        'instructions/instructions2.gif',
        'instructions/instructions3.gif',
        'instructions/instructions4.gif',
        'instructions/comprehension1.png',
        'trials/0/00.png',
        'trials/0/01.png',
        'trials/0/02.png',
        'trials/0/03.png',
        'trials/0/04.png',
        'trials/0/05.png',
        'trials/0/06.png',
        'trials/0/07.png',
        'trials/0/08.png',
        'trials/0/09.png',
        'trials/0/10.png',
        'trials/0/11.png',
        'trials/0/12.png',
        'trials/0/full.gif'
];
