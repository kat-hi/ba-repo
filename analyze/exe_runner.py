import logging
import subprocess


class ExeRunner:

    @staticmethod
    def run(cmd, workingdir):
        try:
            proc = subprocess.run(cmd,
                                  cwd=workingdir,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  errors='ignore',
                                  encoding='utf-8',
                                  universal_newlines=True)
            out = proc.stdout + proc.stderr
            # logging.info(out)
            return out
        except Exception as e:
            logging.error(f'Could not run {cmd}')
            logging.error(e)

