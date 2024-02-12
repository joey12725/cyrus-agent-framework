import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('Your extension for ".cflow", ".agent", and ".function" files is now active!');

    // Example of registering a command. You might want to add specific commands for your languages.
    let disposable = vscode.commands.registerCommand('extension.helloWorld', () => {
        vscode.window.showInformationMessage('Hello World from your Language Extension!');
    });

    context.subscriptions.push(disposable);

    // You can also add language features such as IntelliSense, linters, or formatters here.
    // For simplicity, this example does not include those advanced features.
}

export function deactivate() {
    // This method is called when your extension is deactivated
    console.log('Your extension for ".cflow", ".agent", and ".function" files is now deactivated.');
}
