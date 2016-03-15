module polychord_interface_tools
    use iso_c_binding
    implicit none

    abstract interface
        function c_loglikelihood_type(n, m, theta, phi)
            use iso_c_binding
            integer(c_int), value :: n, m
            real(c_double), dimension(n) :: theta
            real(c_double), dimension(m) :: phi
            real(c_double) :: c_loglikelihood_type
        end function
    end interface

    procedure(c_loglikelihood_type), pointer :: cosmosis_loglikelihood

    contains

    subroutine set_loglikelihood(cosmosis_loglikelihood_input)
        type(c_funptr) :: cosmosis_loglikelihood_input
        call c_f_procpointer(cosmosis_loglikelihood_input, cosmosis_loglikelihood)
    end subroutine

    function loglikelihood(theta,phi)
        double precision, intent(in), dimension(:) :: theta
        double precision, intent(out), dimension(:) :: phi
        double precision :: loglikelihood
        double precision :: logl
        logl = cosmosis_loglikelihood(size(theta), size(phi), theta, phi)
        loglikelihood = logl
    end function



end module polychord_interface_tools


function polychord_cosmosis_interface(nparam, names, nderived, derived_names, cosmosis_output_sub_c, cosmosis_loglikelihood_input) result(status)

    ! ~~~~~~~ Loaded Modules ~~~~~~~
    use ini_module,               only: read_params,initialise_program
    use params_module,            only: add_parameter,param_type
    use priors_module
    use settings_module,          only: program_settings,initialise_settings
    use random_module,            only: initialise_random
    use nested_sampling_module,   only: NestedSampling
    use utils_module,             only: STR_LENGTH
    use abort_module,             only: halt_program
    use polychord_interface_tools,  only: loglikelihood, set_loglikelihood
    use iso_c_binding

    ! ~~~~~~~ Local Variable Declaration ~~~~~~~
    implicit none

    integer(c_int), value :: nparam
    integer(c_int), value :: nderived
    character(kind=c_char, len=nparam*128)  :: names
    character(kind=c_char, len=nderived*128)  :: derived_names

    type(c_funptr),  value :: cosmosis_output_sub_c
    type(c_funptr), value :: cosmosis_loglikelihood_input


    ! Output of the program
    ! 1) mean(log(evidence))
    ! 2) var(log(evidence))
    ! 3) ndead
    ! 4) number of likelihood calls
    ! 5) log(evidence) + log(prior volume)
    real(c_double), dimension(5) :: output_info_c
    integer(c_int) :: status
    character(len=128) :: name
    integer i

    double precision, dimension(5)            :: output_info

    type(program_settings)                    :: settings  ! The program settings 
    type(prior), dimension(:),allocatable     :: priors    ! The details of the priors

    character(len=STR_LENGTH)                 :: input_file     ! input file
    type(param_type),dimension(:),allocatable :: params         ! Parameter array
    type(param_type),dimension(:),allocatable :: derived_params ! Derived parameter array

    write(*,*) " --- Inputs ---"
    write(*,*) nparam
    write(*,*) nderived
    write(*,*) names
    write(*,*) derived_names

    ! ======= (1) Initialisation =======
    ! We need to initialise:
    ! a) mpi threads
    ! b) random number generator
    ! c) priors & settings
    ! d) loglikelihood

    call set_loglikelihood(cosmosis_loglikelihood_input)



    ! ------- (1b) Initialise random number generator -------
    ! Initialise the random number generator with the system time
    ! (Provide an argument to this if you want to set a specific seed
    ! leave argumentless if you want to use the system time)
    call initialise_random()



    ! ------ (1cii) manual setup ------
    ! Here we initialise the array params with all of the details we need
    allocate(params(0),derived_params(0))
    ! The argument to add_parameter are:
    ! 1) params:            the parameter array to add to
    ! 2) name:              paramname for getdist processing
    ! 3) latex:             latex name for getdist processing
    ! 4) speed:             The speed of this parameter (lower => slower)
    ! 5) prior_type:        what kind of prior it is
    ! 6) prior_block:       what other parameters are associated with it
    ! 7) prior_parameters:  parameters of the prior
    !                  array   name     latex     speed  prior_type   prior_block prior_parameters

    do i=1,nparam
        name(1:128) = names(1+(i-1)*128:1+i*128)
        call add_parameter(params,trim(name),trim(name),1, uniform_type,1, [ 0d0 , 1d0 ])
    enddo

    do i=1,nderived
        name = derived_names(1+(i-1)*128:1+i*128)
        call add_parameter(derived_params,trim(name), trim(name))
    enddo

    ! Now initialise the rest of the system settings
    settings%nlive         = 20
    settings%num_repeats   = 4
    settings%do_clustering = .false.

    settings%base_dir      = 'chains'
    settings%file_root     = 'test'

    settings%write_resume  = .false.
    settings%read_resume   = .false.
    settings%write_live    = .false.
    settings%write_stats   = .false.

    settings%equals        = .false.
    settings%posteriors    = .true.
    settings%cluster_posteriors = .false.

    settings%feedback      = 1
    settings%update_files  = settings%nlive

    settings%boost_posterior= 5d0
    allocate(settings%grade_frac(1)) 
    settings%grade_frac=[1d0]

    ! Initialise the program
    call initialise_program(settings,priors,params,derived_params)



    ! ======= (2) Perform Nested Sampling =======
    ! Call the nested sampling algorithm on our chosen likelihood and priors
#ifdef MPI
    output_info = NestedSampling(loglikelihood,priors,settings,MPI_COMM_WORLD, cosmosis_output_sub_c) 
#else
    output_info = NestedSampling(loglikelihood,priors,settings,0, cosmosis_output_sub_c) 
#endif


    ! ======= (3) De-initialise =======

    ! Finish off all of the threads
#ifdef MPI
    call finalise_mpi
#endif

    status = 0


end function
