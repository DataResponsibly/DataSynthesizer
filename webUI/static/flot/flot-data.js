//Flot Pie Chart
$(function () {

    var data = [{
        label: "white",
        data: 6
    }, {
        label: "black",
        data: 1
    }, {
        label: "asian",
        data: 2
    }, {
        label: "Latino",
        data: 3
    }];

    var plotObj = $.plot($("#flot-pie-chart"), data, {
        series: {
            pie: {
                show: true
            }
        },
        grid: {
            hoverable: true
        },
        tooltip: true,
        tooltipOpts: {
            content: "%p.0%, %s", // show percentages, rounding to 2 decimal places
            shifts: {
                x: 20,
                y: 0
            },
            defaultTheme: false
        }
    });

});

$(function () {

    var data = [{
        label: "white",
        data: 5
    }, {
        label: "black",
        data: 4
    }, {
        label: "asian",
        data: 1
    }, {
        label: "Latino",
        data: 2
    }];

    var plotObj = $.plot($("#flot-pie-chart2"), data, {
        series: {
            pie: {
                show: true
            }
        },
        grid: {
            hoverable: true
        },
        tooltip: true,
        tooltipOpts: {
            content: "%p.0%, %s", // show percentages, rounding to 2 decimal places
            shifts: {
                x: 20,
                y: 0
            },
            defaultTheme: false
        }
    });

});