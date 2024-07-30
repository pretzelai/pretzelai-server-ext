import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * Initialization data for the pretzelai-server extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'pretzelai-server:plugin',
  description: "Pretzel's Server Extension",
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension pretzelai-server is activated!');
  }
};

export default plugin;
