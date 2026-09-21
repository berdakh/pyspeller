"""Command line entry points: `python -m pyspeller <command>`.

Each component is a separate process in normal use:

    python -m pyspeller buffer            # the data/event server
    python -m pyspeller simulator         # a fake amplifier ...
    python -m pyspeller lsl --list        # ... or a real one over LSL
    python -m pyspeller sigproc           # the online signal processing
    python -m pyspeller speller           # the stimulus display
    python -m pyspeller gui               # control panel + live signals

`python -m pyspeller run` starts all of them in one process, and
`python -m pyspeller demo` runs a whole experiment without any display.
"""
import argparse
import threading

from .config import SpellerConfig


def _config_from_args(args):
    config = SpellerConfig(host=args.host, port=args.port)
    for field in ('speed', 'n_repetitions', 'isi', 'fsample'):
        value = getattr(args, field, None)
        if value is not None:
            setattr(config, field, value)
    return config


def _add_common(parser):
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=1972)
    parser.add_argument('--speed', type=float, default=1.0,
                        help='compress experiment time by this factor')
    parser.add_argument('--n-repetitions', type=int, default=None,
                        help='flashes of each row/column per letter')
    parser.add_argument('--isi', type=float, default=None,
                        help='seconds between flash onsets')
    parser.add_argument('--fsample', type=float, default=None)


# -- individual components -------------------------------------------------
def cmd_buffer(args):
    from .buffer.server import main as server_main
    server_main(['--host', args.host, '--port', str(args.port)])


def cmd_simulator(args):
    from .acquisition.simulator import main as sim_main
    sim_main(['--host', args.host, '--port', str(args.port),
              '--speed', str(args.speed),
              '--erp-amplitude', str(args.erp_amplitude),
              '--noise-amplitude', str(args.noise_amplitude)])


def cmd_lsl(args):
    from .acquisition.lsl_bridge import main as lsl_main
    argv = ['--host', args.host, '--port', str(args.port)]
    if args.list:
        argv.append('--list')
    if args.name:
        argv += ['--name', args.name]
    argv += ['--type', args.type]
    lsl_main(argv)


def cmd_lsl_publish(args):
    """Publish the buffer's samples as an LSL stream (to test the LSL path)."""
    from .acquisition.lsl_outlet import LSLOutlet
    outlet = LSLOutlet(args.host, args.port, args.name, args.type)
    print('publishing buffer %s:%d as LSL stream %r'
          % (args.host, args.port, args.name), flush=True)
    try:
        outlet.run()
    except KeyboardInterrupt:
        pass


def cmd_speller(args):
    from .buffer.client import BufferClient
    from .clock import BufferClock, Clock
    from .speller.matrix import SpellerMatrix
    from .speller.render import make_renderer
    from .speller.stimulus import SpellerStimulus

    config = _config_from_args(args)
    client = BufferClient(config.host, config.port).connect(retries=20)
    client.wait_for_header(timeout=60)
    renderer = make_renderer(args.display, SpellerMatrix(config.symbols))
    clock = (BufferClock(client, config.fsample, config.speed) if config.speed != 1
             else Clock(1.0))
    stimulus = SpellerStimulus(client, config, renderer, clock)
    print('speller ready -- waiting for startPhase.cmd events', flush=True)
    worker = threading.Thread(target=stimulus.run_phase_loop, daemon=True)
    worker.start()
    renderer.mainloop(worker)


def cmd_sigproc(args):
    from .buffer.client import BufferClient
    from .speller.sigproc import SignalProcessor

    config = _config_from_args(args)
    client = BufferClient(config.host, config.port).connect(retries=20)
    client.wait_for_header(timeout=60)
    processor = SignalProcessor(client, config)
    print('signal processing ready -- waiting for startPhase.cmd events', flush=True)
    processor.run_phase_loop(model_path=args.model)


def cmd_gui(args):
    from .gui.control_panel import ControlPanel
    ControlPanel(_config_from_args(args)).run()


# -- everything at once ----------------------------------------------------
def cmd_demo(args):
    from .experiment import run_demo
    config = _config_from_args(args)
    config.port = 0                       # pick a free port
    run_demo(config, erp_amplitude=args.erp_amplitude,
             noise_amplitude=args.noise_amplitude, renderer=args.display)


def cmd_run(args):
    """Buffer, amplifier, speller, signal processing and GUI in one process."""
    from .acquisition.simulator import EEGSimulator
    from .buffer.client import BufferClient
    from .buffer.server import BufferServer
    from .clock import BufferClock, Clock
    from .gui.control_panel import ControlPanel
    from .speller.matrix import SpellerMatrix
    from .speller.render import TkRenderer
    from .speller.sigproc import SignalProcessor
    from .speller.stimulus import SpellerStimulus

    config = _config_from_args(args)
    server = simulator = bridge = None
    if not args.no_buffer:
        server = BufferServer(config.host, config.port).start()
        config.port = server.port
        print('buffer server on %s:%d' % (config.host, config.port))

    if args.lsl:
        from .acquisition.lsl_bridge import LSLBridge
        bridge = LSLBridge(config.host, config.port, args.lsl_name,
                           args.lsl_type).start()
        config.fsample = bridge.fsample
        config.channels = tuple(bridge.labels)
    else:
        simulator = EEGSimulator(config, Clock(config.speed),
                                 erp_amplitude=args.erp_amplitude,
                                 noise_amplitude=args.noise_amplitude).start()

    stim_client = BufferClient(config.host, config.port).connect(retries=20)
    stim_client.wait_for_header(timeout=60)
    proc_client = BufferClient(config.host, config.port).connect(retries=20)
    proc_client.wait_for_header(timeout=60)

    stop = threading.Event()
    panel = ControlPanel(config, on_quit=stop.set)
    renderer = TkRenderer(SpellerMatrix(config.symbols), master=panel.root)
    panel.renderers.append(renderer)

    clock = (BufferClock(stim_client, config.fsample, config.speed)
             if config.speed != 1 else Clock(1.0))
    stimulus = SpellerStimulus(stim_client, config, renderer, clock)
    processor = SignalProcessor(proc_client, config)
    threads = [threading.Thread(target=stimulus.run_phase_loop, args=(stop,),
                                daemon=True),
               threading.Thread(target=processor.run_phase_loop,
                                args=(stop, args.model), daemon=True)]
    for thread in threads:
        thread.start()

    try:
        panel.run()
    finally:
        stop.set()
        for component in (simulator, bridge, server):
            if component is not None:
                component.stop()


def build_parser():
    parser = argparse.ArgumentParser(prog='pyspeller',
                                     description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)

    for name, handler in [('buffer', cmd_buffer), ('simulator', cmd_simulator),
                          ('lsl', cmd_lsl), ('lsl-publish', cmd_lsl_publish),
                          ('speller', cmd_speller),
                          ('sigproc', cmd_sigproc), ('gui', cmd_gui),
                          ('demo', cmd_demo), ('run', cmd_run)]:
        p = sub.add_parser(name, help=handler.__doc__ or ('run the %s' % name))
        _add_common(p)
        p.set_defaults(func=handler)
        if name in ('simulator', 'demo', 'run'):
            p.add_argument('--erp-amplitude', type=float, default=8.0)
            p.add_argument('--noise-amplitude', type=float, default=10.0)
        if name in ('speller', 'demo'):
            p.add_argument('--display', default='tk' if name == 'speller' else 'text',
                           choices=['tk', 'text', 'headless', 'none'])
        if name in ('sigproc', 'run'):
            p.add_argument('--model', default=None,
                           help='file to save the trained classifier to')
        if name == 'lsl':
            p.add_argument('--list', action='store_true')
            p.add_argument('--name', default=None)
            p.add_argument('--type', default='EEG')
        if name == 'lsl-publish':
            p.add_argument('--name', default='pyspeller-sim')
            p.add_argument('--type', default='EEG')
        if name == 'run':
            p.add_argument('--no-buffer', action='store_true',
                           help='connect to a buffer that is already running')
            p.add_argument('--lsl', action='store_true',
                           help='take data from an LSL device instead of the simulator')
            p.add_argument('--lsl-name', default=None)
            p.add_argument('--lsl-type', default='EEG')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == '__main__':
    main()
