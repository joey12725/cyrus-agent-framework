const vscode = require('vscode');

function activate(context) {
    console.log('Your extension for ".cflow", ".agent", and ".function" files is now active!');

    let disposable = vscode.commands.registerCommand('extension.helloWorld', function () {
        vscode.window.showInformationMessage('Hello World from your Language Extension!');
    });

    context.subscriptions.push(disposable);
}

function deactivate() {
    console.log('Your extension for ".cflow", ".agent", and ".function" files is now deactivated.');
}

exports.activate = activate;
exports.deactivate = deactivate;
