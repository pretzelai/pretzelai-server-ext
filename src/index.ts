import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './handler';

/**
 * Initialization data for the pretzelai-server extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'pretzelai-server:plugin',
  description: "Pretzel's Server Extension",
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension pretzelai-server is activated!');

    requestAPI<any>('get-example')
      .then(data => {
        console.log(data);
      })
      .catch(reason => {
        console.error(
          `The pretzelai_server server extension appears to be missing.\n${reason}`
        );
      });
  }
};

export default plugin;
